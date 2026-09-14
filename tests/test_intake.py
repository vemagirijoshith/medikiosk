from unittest.mock import AsyncMock, patch


VALID_AI_RESPONSE = (
    '{"assistant_message":"When did it start?","status":"collecting",'
    '"clinical_data":{"chief_complaint":"fever and headache",'
    '"duration":"two days","severity":null,"location":null,"character":null},'
    '"red_flags":[],"next_section":"symptom_details"}'
)


def test_intake_start_initializes_session_without_ai(client, synthetic_patient):
    test_client, _ = client
    with patch("app.api.intake.generate_clinical_response") as ai_call:
        response = test_client.post(
            "/intake/start", json={"patient_id": synthetic_patient["id"]}
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["encounter_id"] > 0
    assert payload["status"] == "collecting"
    assert payload["assistant_message"]
    ai_call.assert_not_called()


def test_intake_message_success_updates_conversation_and_persists(
    client, synthetic_patient
):
    test_client, session_factory = client
    start = test_client.post(
        "/intake/start", json={"patient_id": synthetic_patient["id"]}
    ).json()
    with patch(
        "app.api.intake.generate_clinical_response",
        new=AsyncMock(return_value=VALID_AI_RESPONSE),
    ) as ai_call:
        response = test_client.post(
            "/intake/message",
            json={
                "encounter_id": start["encounter_id"],
                "message": "I have had fever and headache for two days.",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_message"] == "When did it start?"
    assert payload["extracted_data"]["chief_complaint"] == "fever and headache"
    ai_call.assert_awaited_once()
    assert ai_call.await_args.args[0][0] == {
        "role": "user",
        "content": "I have had fever and headache for two days.",
    }
    assert ai_call.await_args.args[0][1] == {
        "role": "assistant",
        "content": "When did it start?",
    }
    db = session_factory()
    try:
        from app.models import Encounter, Symptom

        encounter = db.get(Encounter, start["encounter_id"])
        symptom = db.query(Symptom).filter_by(encounter_id=encounter.id).one()
        assert encounter.chief_complaint == "fever and headache"
        assert symptom.duration == "two days"
    finally:
        db.close()


def test_intake_validation_and_not_found(client):
    test_client, _ = client
    assert test_client.post("/intake/start", json={"patient_id": 99999}).status_code == 404
    assert test_client.post(
        "/intake/message", json={"encounter_id": 99999, "message": "hello"}
    ).status_code == 404
    assert test_client.post(
        "/intake/message", json={"encounter_id": 1, "message": "   "}
    ).status_code == 422
    assert test_client.post("/intake/start", json={"patient_id": "bad"}).status_code == 422


def test_intake_provider_errors_are_safe(client, synthetic_patient):
    test_client, _ = client
    start = test_client.post(
        "/intake/start", json={"patient_id": synthetic_patient["id"]}
    ).json()
    from app.services.ai_service import AIRateLimitError, AITimeoutError, AIConnectionError

    for exception, expected_status, expected_detail in [
        (AIRateLimitError(), 503, "AI provider is temporarily unavailable. Please try again later."),
        (AITimeoutError(), 504, "AI provider request timed out."),
        (AIConnectionError(), 503, "AI provider could not be reached."),
    ]:
        with patch(
            "app.api.intake.generate_clinical_response",
            new=AsyncMock(side_effect=exception),
        ):
            response = test_client.post(
                "/intake/message",
                json={"encounter_id": start["encounter_id"], "message": "I feel unwell."},
            )
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_detail


def test_malformed_ai_response_returns_safe_error_and_does_not_persist(
    client, synthetic_patient
):
    test_client, session_factory = client
    start = test_client.post(
        "/intake/start", json={"patient_id": synthetic_patient["id"]}
    ).json()
    with patch(
        "app.api.intake.generate_clinical_response",
        new=AsyncMock(return_value="not valid JSON"),
    ):
        response = test_client.post(
            "/intake/message",
            json={"encounter_id": start["encounter_id"], "message": "I feel unwell."},
        )
    assert response.status_code == 502
    db = session_factory()
    try:
        from app.models import Encounter, Symptom

        encounter = db.get(Encounter, start["encounter_id"])
        assert encounter.chief_complaint is None
        assert db.query(Symptom).filter_by(encounter_id=encounter.id).count() == 0
    finally:
        db.close()


def test_parse_ai_output_normalizes_string_red_flags_and_numeric_severity():
    from app.api.intake import _parse_ai_output

    sample_ai_json = '''{
        "assistant_message": "మీకు వాంతులు లేదా కళ్లు తిరగడం వంటి ఇతర లక్షణాలు ఏమైనా ఉన్నాయా?",
        "status": "collecting",
        "clinical_data": {
            "chief_complaint": "తీవ్రమైన తలనొప్పి",
            "onset": null,
            "duration": null,
            "location": "తల",
            "severity": 10,
            "character": null,
            "timing": null,
            "aggravating_factors": [],
            "relieving_factors": [],
            "associated_symptoms": [],
            "medical_history": [],
            "medications": [],
            "allergies": [],
            "relevant_history": []
        },
        "red_flags": [
            "Severe headache rated 10/10"
        ],
        "next_section": "onset"
    }'''
    output = _parse_ai_output(sample_ai_json)
    assert output.status == "collecting"
    assert len(output.red_flags) == 1
    assert output.red_flags[0].message == "Severe headache rated 10/10"
    assert output.red_flags[0].severity == "high"
    assert output.clinical_data["severity"] == 10