const chat = document.getElementById("chat");
const composer = document.getElementById("composer");
const input = document.getElementById("messageInput");
const chipRow = document.getElementById("chipRow");
const sendButton = composer.querySelector("button");

function addMessage(text, role, toolUsed) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  if (toolUsed) {
    const tag = document.createElement("span");
    tag.className = "tool-tag";
    tag.textContent = `tool used: ${toolUsed}`;
    bubble.appendChild(tag);
  }

  wrapper.appendChild(bubble);
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
  return wrapper;
}

function addErrorMessage(text, onRetry) {
  const wrapper = document.createElement("div");
  wrapper.className = "message assistant";

  const bubble = document.createElement("div");
  bubble.className = "bubble bubble-error";
  bubble.textContent = text;

  if (onRetry) {
    const retryBtn = document.createElement("button");
    retryBtn.className = "retry-link";
    retryBtn.type = "button";
    retryBtn.textContent = "Try again";
    retryBtn.addEventListener("click", () => {
      wrapper.remove();
      onRetry();
    });
    bubble.appendChild(document.createElement("br"));
    bubble.appendChild(retryBtn);
  }

  wrapper.appendChild(bubble);
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
}

function addTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "message assistant";
  wrapper.id = "typingIndicator";

  const bubble = document.createElement("div");
  bubble.className = "bubble typing-bubble";
  bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

  wrapper.appendChild(bubble);
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function setInputLocked(locked) {
  input.disabled = locked;
  sendButton.disabled = locked;
  chipRow.querySelectorAll(".chip").forEach((c) => (c.disabled = locked));
}

async function sendMessage(message, { showUserBubble = true } = {}) {
  if (showUserBubble) {
    addMessage(message, "user");
    input.value = "";
  }
  setInputLocked(true);
  addTypingIndicator();

  let response;
  try {
    response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  } catch (networkErr) {
    // fetch itself threw: no connection, DNS failure, CORS, etc.
    removeTypingIndicator();
    setInputLocked(false);
    addErrorMessage(
      "Can't reach the server right now. Check your connection and try again.",
      () => sendMessage(message, { showUserBubble: false })
    );
    console.error("Network error:", networkErr);
    return;
  }

  removeTypingIndicator();
  setInputLocked(false);

  if (!response.ok) {
    // server reachable but responded with an error status (4xx/5xx)
    let detail = `Server error (${response.status}).`;
    try {
      const errBody = await response.json();
      if (errBody.error) detail = errBody.error;
    } catch (_) {
      // response wasn't JSON; keep the generic status message
    }
    addErrorMessage(`${detail} Please try again.`, () =>
      sendMessage(message, { showUserBubble: false })
    );
    return;
  }

  const data = await response.json();

  if (data.error) {
    // 200 OK but the API reported a logical error (e.g. empty message edge case)
    addErrorMessage(data.error, null);
    return;
  }

  addMessage(data.reply, "assistant", data.tool_used);
  if (voiceOutputEnabled) speakText(data.reply);
}

composer.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (message) sendMessage(message);
});

chipRow.addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (chip && !chip.disabled) sendMessage(chip.dataset.message);
});

// ---------------------------------------------------------------------
// Voice: speech-to-text input (mic button) and text-to-speech output
// (speaker toggle). Both are optional, additive layers on top of the
// existing text chat - if the browser doesn't support one or both APIs,
// the relevant button just disables itself with an explanatory title
// rather than breaking anything.
// ---------------------------------------------------------------------

const micButton = document.getElementById("micButton");
const voiceOutputToggle = document.getElementById("voiceOutputToggle");
let voiceOutputEnabled = false;

// --- Voice input (speech-to-text) ---
const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognitionAPI) {
  micButton.disabled = true;
  micButton.title = "Voice input isn't supported in this browser (try Chrome or Edge)";
} else {
  const recognition = new SpeechRecognitionAPI();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  let listening = false;

  micButton.addEventListener("click", () => {
    if (listening) {
      recognition.stop();
      return;
    }
    try {
      recognition.start();
    } catch (err) {
      // start() throws if called while already starting/running in some
      // browsers - safe to ignore, the existing session continues.
      console.error("Speech recognition failed to start:", err);
    }
  });

  recognition.addEventListener("start", () => {
    listening = true;
    micButton.classList.add("listening");
    micButton.setAttribute("aria-pressed", "true");
  });

  recognition.addEventListener("end", () => {
    listening = false;
    micButton.classList.remove("listening");
    micButton.setAttribute("aria-pressed", "false");
  });

  recognition.addEventListener("result", (event) => {
    const transcript = event.results[0][0].transcript;
    if (transcript.trim()) {
      sendMessage(transcript.trim());
    }
  });

  recognition.addEventListener("error", (event) => {
    listening = false;
    micButton.classList.remove("listening");
    micButton.setAttribute("aria-pressed", "false");
    // Common cases: 'not-allowed' (mic permission denied, or page isn't
    // on HTTPS/localhost), 'no-speech' (timed out with no input).
    console.error("Speech recognition error:", event.error);
    if (event.error === "not-allowed") {
      addErrorMessage(
        "Microphone access was blocked. Voice input needs either HTTPS or localhost, and mic permission.",
        null
      );
    }
  });
}

// --- Voice output (text-to-speech) ---
if (!("speechSynthesis" in window)) {
  voiceOutputToggle.disabled = true;
  voiceOutputToggle.title = "Spoken replies aren't supported in this browser";
} else {
  voiceOutputToggle.addEventListener("click", () => {
    voiceOutputEnabled = !voiceOutputEnabled;
    voiceOutputToggle.setAttribute("aria-pressed", String(voiceOutputEnabled));
    voiceOutputToggle.textContent = voiceOutputEnabled ? "🔊" : "🔇";
    voiceOutputToggle.title = voiceOutputEnabled
      ? "Spoken replies on - click to mute"
      : "Toggle spoken replies";
    if (!voiceOutputEnabled) window.speechSynthesis.cancel();
  });
}

function speakText(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel(); // don't let replies queue up and overlap
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  window.speechSynthesis.speak(utterance);
}

