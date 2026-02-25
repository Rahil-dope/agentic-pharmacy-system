/**
 * Agentic Pharmacy Assistant - Frontend Logic
 */

const API_BASE = "http://localhost:8000/api";

document.addEventListener("DOMContentLoaded", () => {
  // UI Elements
  const chatView = document.getElementById("chat-view");
  const adminView = document.getElementById("admin-view");
  const btnChat = document.getElementById("btn-chat");
  const btnAdmin = document.getElementById("btn-admin");
  const chatMessages = document.getElementById("chat-messages");
  const userInput = document.getElementById("user-input");
  const customerIdInput = document.getElementById("customer-id");
  const btnSend = document.getElementById("btn-send");
  const btnVoice = document.getElementById("btn-voice");
  const tableRefills = document.querySelector("#table-refills tbody");
  const tableInventory = document.querySelector("#table-inventory tbody");

  /**
   * View Switching
   */
  btnChat.addEventListener("click", () => {
    chatView.style.display = "flex";
    adminView.style.display = "none";
    btnChat.classList.add("active");
    btnAdmin.classList.remove("active");
  });

  btnAdmin.addEventListener("click", () => {
    chatView.style.display = "none";
    adminView.style.display = "block";
    btnChat.classList.remove("active");
    btnAdmin.classList.add("active");
    loadAdminData();
  });

  /**
   * Chat Logic
   */
  async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    const customerId = parseInt(customerIdInput.value, 10) || 1;

    // Display user message
    appendMessage("user", text);
    userInput.value = "";
    userInput.focus();

    // Show typing indicator
    const typingEl = appendTypingIndicator();

    try {
      const response = await fetch(`${API_BASE}/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          message: text
        })
      });

      typingEl.remove();

      if (!response.ok) {
        const errText = await response.text().catch(() => "Unknown error");
        throw new Error(`Backend error (${response.status}): ${errText}`);
      }

      const data = await response.json();
      const { response: agentResult, trace_url } = data;

      // Guard against undefined message
      const message = agentResult?.message ?? agentResult?.status ?? "No response from agent.";
      appendMessage("agent", message, trace_url);
    } catch (error) {
      typingEl.remove();
      console.error(error);
      appendMessage("agent", "⚠️ " + error.message, null, true);
    }
  }

  function appendTypingIndicator() {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message agent";
    const bubble = document.createElement("div");
    bubble.className = "bubble typing";
    bubble.innerHTML = '<span></span><span></span><span></span>';
    msgDiv.appendChild(bubble);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv;
  }

  function appendMessage(role, text, traceUrl = null, isError = false) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble" + (isError ? " error-bubble" : "");
    bubble.textContent = text;
    msgDiv.appendChild(bubble);

    if (traceUrl) {
      const link = document.createElement("a");
      link.className = "trace-link";
      link.href = traceUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "🔍 View Trace in Langfuse";
      msgDiv.appendChild(link);
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  btnSend.addEventListener("click", sendMessage);
  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });

  /**
   * Admin Dashboard Data
   */
  async function loadAdminData() {
    tableRefills.innerHTML = '<tr><td colspan="3" class="loading-cell">Loading…</td></tr>';
    tableInventory.innerHTML = '<tr><td colspan="3" class="loading-cell">Loading…</td></tr>';

    try {
      // Load Refills
      const refillRes = await fetch(`${API_BASE}/admin/refill-alerts`);
      if (!refillRes.ok) throw new Error(`Refill alerts request failed (${refillRes.status})`);
      const refills = await refillRes.json();
      tableRefills.innerHTML = refills.length
        ? refills.map(r => `
          <tr>
            <td>${r.customer_id}</td>
            <td>${r.medicine_name}</td>
            <td>${r.days_overdue}</td>
          </tr>
        `).join("")
        : '<tr><td colspan="3" style="text-align:center;color:var(--text-muted)">No alerts</td></tr>';
    } catch (error) {
      console.error("Failed to load refill alerts:", error);
      tableRefills.innerHTML = `<tr><td colspan="3" class="error-cell">Failed to load: ${error.message}</td></tr>`;
    }

    try {
      // Load Inventory
      const invRes = await fetch(`${API_BASE}/medicines/`);
      if (!invRes.ok) throw new Error(`Medicines request failed (${invRes.status})`);
      const medicines = await invRes.json();
      tableInventory.innerHTML = medicines.length
        ? medicines.map(m => `
          <tr>
            <td>${m.name}</td>
            <td>${m.stock_quantity}</td>
            <td>
              <span class="prescription-badge ${m.prescription_required ? '' : 'none-badge'}">
                ${m.prescription_required ? 'Required' : 'None'}
              </span>
            </td>
          </tr>
        `).join("")
        : '<tr><td colspan="3" style="text-align:center;color:var(--text-muted)">No inventory</td></tr>';
    } catch (error) {
      console.error("Failed to load inventory:", error);
      tableInventory.innerHTML = `<tr><td colspan="3" class="error-cell">Failed to load: ${error.message}</td></tr>`;
    }
  }

  /**
   * Voice Input (Web Speech API)
   */
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    btnVoice.addEventListener("click", () => {
      btnVoice.classList.add("listening");
      recognition.start();
    });

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      userInput.value = transcript;
      btnVoice.classList.remove("listening");
    };

    recognition.onerror = () => {
      btnVoice.classList.remove("listening");
    };

    recognition.onend = () => {
      btnVoice.classList.remove("listening");
    };
  } else {
    btnVoice.style.display = "none"; // Hide if not supported
  }
});
