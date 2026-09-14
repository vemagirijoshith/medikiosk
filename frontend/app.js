const state = { patientId: null, encounterId: null, language: "en", lastQuestion: "" };
const $ = (selector) => document.querySelector(selector);

function openNurseDialog() { $("#nurse-dialog").showModal(); }
$("#nurse-button").addEventListener("click", openNurseDialog);
$("#side-nurse").addEventListener("click", openNurseDialog);
$("#cancel-nurse").addEventListener("click", () => $("#nurse-dialog").close());
$("#confirm-nurse").addEventListener("click", () => {
  $("#nurse-dialog").close();
  $("#form-status").textContent = "A staff member has been notified and is coming to this kiosk.";
});

document.querySelectorAll("[data-language]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-language]").forEach((item) => item.classList.remove("selected"));
    button.classList.add("selected");
    state.language = button.dataset.language;
  });
});

function addBubble(text, type) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${type}`;
  bubble.textContent = text;
  $("#conversation").appendChild(bubble);
  bubble.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "The service could not complete that request.");
  return data;
}

$("#patient-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const status = $("#form-status");
  status.textContent = "Creating your secure visit...";
  try {
    const patient = await api("/patients/", { method: "POST", body: JSON.stringify({ name: form.get("name"), age: Number(form.get("age")), gender: form.get("gender"), phone: form.get("phone") || null, language: state.language }) });
    const encounter = await api("/intake/start", { method: "POST", body: JSON.stringify({ patient_id: patient.id, language: state.language, mode: "general" }) });
    state.patientId = patient.id;
    state.encounterId = encounter.encounter_id;
    $("#patient-name").textContent = patient.name.split(" ")[0];
    $("#conversation").replaceChildren();
    addBubble(encounter.assistant_message, "assistant");
    $("#check-in").classList.add("hidden");
    $("#intake").classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (error) { status.textContent = error.message; }
});

$("#message-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = $("#message-input");
  const message = input.value.trim();
  if (!message) return;
  const status = $("#message-status");
  addBubble(message, "user");
  input.value = "";
  status.textContent = "MediKiosk is preparing the next question...";
  try {
    const result = await api("/intake/message", { method: "POST", body: JSON.stringify({ encounter_id: state.encounterId, message }) });
    addBubble(result.assistant_message, "assistant");
    $("#intake-status").textContent = result.status === "needs_staff_attention" ? "Staff attention requested" : result.status === "ready_for_review" ? "Ready for doctor review" : "Collecting history";
    if (result.red_flags.length) status.textContent = "A possible urgent symptom was flagged for staff review.";
    else status.textContent = "";
  } catch (error) { status.textContent = error.message; }
});

$("#voice-mode").addEventListener("click", () => $("#patient-form input[name=name]").focus());
$("#touch-mode").addEventListener("click", () => $("#patient-form input[name=name]").focus());
$("#repeat-button").addEventListener("click", () => {
  const last = [...document.querySelectorAll(".bubble.assistant")].pop();
  if (last && "speechSynthesis" in window) window.speechSynthesis.speak(new SpeechSynthesisUtterance(last.textContent));
});
$("#audio-button").addEventListener("click", () => {
  if ("speechSynthesis" in window) window.speechSynthesis.speak(new SpeechSynthesisUtterance("Welcome to MediKiosk. Choose a language and tell us how we can help."));
});
$("#mic-button").addEventListener("click", () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) { $("#message-status").textContent = "Voice input is not available in this browser. You can type your answer instead."; return; }
  const recognition = new SpeechRecognition();
  recognition.lang = state.language === "hi" ? "hi-IN" : state.language === "ta" ? "ta-IN" : "en-IN";
  recognition.onresult = (event) => { $("#message-input").value = event.results[0][0].transcript; };
  recognition.onerror = () => { $("#message-status").textContent = "We could not hear that. Please try again or type your answer."; };
  recognition.start();
});