function toggleEdit(filename) {
  const form = document.getElementById("edit-" + filename);
  form.style.display = form.style.display === "none" ? "flex" : "none";
}

function addChatMessage(who, text, pending) {
  const log = document.getElementById("chat-log");
  const el = document.createElement("div");
  el.className = "chat-msg" + (pending ? " pending" : "");
  el.innerHTML = `<div class="who">${who}</div><div class="text"></div>`;
  el.querySelector(".text").textContent = text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  addChatMessage("you", message, false);
  input.value = "";
  const pendingEl = addChatMessage("figaro", "thinking...", true);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();
    pendingEl.classList.remove("pending");
    pendingEl.querySelector(".text").textContent = data.reply || "(no response)";
  } catch (err) {
    pendingEl.classList.remove("pending");
    pendingEl.querySelector(".text").textContent = "Error reaching Figaro: " + err;
  }
});
