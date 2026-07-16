/* Summer Front chat widget
   Little popup bubble in the bottom-right corner. It talks to /api/chat on
   our own domain rather than hitting OpenRouter directly, which is what
   keeps the API key on the server instead of sitting exposed in this file.
*/
(function () {
  "use strict";

  // Not actually used for anything anymore - model selection moved server
  // side - keeping the list here just so it's obvious what's available.
  var MODEL_FALLBACKS = [
    "openrouter/free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-120b:free",
    "qwen/qwen3-coder:free",
  ];

  var widgetCss =
    "#sf-chat-btn{position:fixed;bottom:24px;right:24px;z-index:9999;width:60px;height:60px;border-radius:50%;" +
    "background:var(--coral,#FF6B4A);color:#fff;border:none;box-shadow:0 10px 30px rgba(22,36,28,.25);" +
    "display:flex;align-items:center;justify-content:center;cursor:pointer;transition:transform .2s ease}" +
    "#sf-chat-btn:hover{transform:scale(1.06)}" +
    "#sf-chat-btn svg{width:26px;height:26px}" +
    "#sf-chat-btn .close-icon{display:none}" +
    "#sf-chat-btn.open .bubble-icon{display:none}" +
    "#sf-chat-btn.open .close-icon{display:block}" +
    "#sf-chat-box{position:fixed;bottom:96px;right:24px;z-index:9999;width:360px;max-width:calc(100vw - 32px);" +
    "height:520px;max-height:calc(100vh - 140px);background:#fff;border-radius:18px;" +
    "box-shadow:0 20px 60px rgba(22,36,28,.28);display:flex;flex-direction:column;overflow:hidden;" +
    "font-family:var(--sans,'Inter',sans-serif);opacity:0;transform:translateY(16px) scale(.98);" +
    "pointer-events:none;transition:opacity .22s ease,transform .22s ease;border:1px solid var(--line,#E4DCC6)}" +
    "#sf-chat-box.open{opacity:1;transform:none;pointer-events:auto}" +
    "#sf-chat-topbar{background:var(--teal,#1F5C56);color:#fff;padding:16px 18px;display:flex;" +
    "align-items:center;justify-content:space-between}" +
    "#sf-chat-topbar b{font-family:var(--serif,'Fraunces',serif);font-size:16px}" +
    "#sf-chat-topbar span{font-size:11.5px;opacity:.8}" +
    "#sf-chat-x{background:rgba(255,255,255,.14);border:none;color:#fff;width:30px;height:30px;border-radius:50%;" +
    "cursor:pointer}" +
    "#sf-chat-log{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;" +
    "background:var(--cream,#FBF6EA)}" +
    ".bubble{max-width:82%;padding:10px 13px;border-radius:14px;font-size:13.5px;line-height:1.45;" +
    "white-space:pre-wrap;word-wrap:break-word}" +
    ".bubble.bot{align-self:flex-start;background:#fff;border:1px solid var(--line,#E4DCC6);border-bottom-left-radius:4px}" +
    ".bubble.user{align-self:flex-end;background:var(--coral,#FF6B4A);color:#fff;border-bottom-right-radius:4px}" +
    ".bubble.thinking span{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--teal,#1F5C56);" +
    "opacity:.4;margin-right:3px;animation:sfDot 1s infinite ease-in-out}" +
    ".bubble.thinking span:nth-child(2){animation-delay:.15s}" +
    ".bubble.thinking span:nth-child(3){animation-delay:.3s}" +
    "@keyframes sfDot{0%,80%,100%{transform:translateY(0);opacity:.4}40%{transform:translateY(-4px);opacity:1}}" +
    "#sf-chat-form{display:flex;gap:8px;padding:12px;border-top:1px solid var(--line,#E4DCC6);background:#fff}" +
    "#sf-chat-input{flex:1;border:1px solid var(--line,#E4DCC6);border-radius:22px;padding:10px 16px;" +
    "font-size:13.5px;font-family:inherit;outline:none;background:var(--cream,#FBF6EA)}" +
    "#sf-chat-input:focus{border-color:var(--coral,#FF6B4A)}" +
    "#sf-chat-go{width:38px;height:38px;border-radius:50%;border:none;background:var(--coral,#FF6B4A);color:#fff;" +
    "cursor:pointer;flex-shrink:0}" +
    "#sf-chat-go:disabled{opacity:.5}" +
    "@media (max-width:480px){#sf-chat-box{right:16px;left:16px;width:auto;bottom:88px}#sf-chat-btn{right:16px;bottom:16px}}";

  var styleTag = document.createElement("style");
  styleTag.textContent = widgetCss;
  document.head.appendChild(styleTag);

  var toggleBtn = document.createElement("button");
  toggleBtn.id = "sf-chat-btn";
  toggleBtn.setAttribute("aria-label", "Chat with Summer Front");
  toggleBtn.innerHTML =
    '<svg class="bubble-icon" viewBox="0 0 24 24" fill="none"><path d="M4 4h16v12H7l-3 3V4z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>' +
    '<svg class="close-icon" viewBox="0 0 24 24" fill="none"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>';

  var chatBox = document.createElement("div");
  chatBox.id = "sf-chat-box";
  chatBox.innerHTML =
    '<div id="sf-chat-topbar"><div><b>Summer Front</b><br><span>Ask us anything</span></div>' +
    '<button id="sf-chat-x" aria-label="Close chat">\u2715</button></div>' +
    '<div id="sf-chat-log"></div>' +
    '<form id="sf-chat-form">' +
    '<input id="sf-chat-input" type="text" autocomplete="off" placeholder="Ask about the menu, locations\u2026">' +
    '<button id="sf-chat-go" type="submit" aria-label="Send">\u27a4</button>' +
    "</form>";

  // Small helper so we don't have to worry about whether the DOM is ready yet
  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  onReady(function () {
    document.body.appendChild(toggleBtn);
    document.body.appendChild(chatBox);

    var logEl = chatBox.querySelector("#sf-chat-log");
    var formEl = chatBox.querySelector("#sf-chat-form");
    var inputEl = chatBox.querySelector("#sf-chat-input");
    var sendBtn = chatBox.querySelector("#sf-chat-go");

    var conversation = []; // { role, content } pairs sent back to the server each time
    var isOpen = false;
    var hasGreeted = false;

    function addBubble(role, text) {
      var bubble = document.createElement("div");
      bubble.className = "bubble " + (role === "user" ? "user" : "bot");
      bubble.textContent = text;
      logEl.appendChild(bubble);
      logEl.scrollTop = logEl.scrollHeight;
      return bubble;
    }

    function addThinkingBubble() {
      var bubble = document.createElement("div");
      bubble.className = "bubble bot thinking";
      bubble.innerHTML = "<span></span><span></span><span></span>";
      logEl.appendChild(bubble);
      logEl.scrollTop = logEl.scrollHeight;
      return bubble;
    }

    toggleBtn.addEventListener("click", function () {
      isOpen = !isOpen;
      chatBox.classList.toggle("open", isOpen);
      toggleBtn.classList.toggle("open", isOpen);

      if (isOpen && !hasGreeted) {
        hasGreeted = true;
        addBubble("bot", "Hey there! Welcome to Summer Front. Ask me about the menu, our locations, or how to book - happy to help.");
      }

      if (isOpen) {
        // give the open animation a moment before stealing focus
        setTimeout(function () {
          inputEl.focus();
        }, 150);
      }
    });

    chatBox.querySelector("#sf-chat-x").addEventListener("click", function () {
      isOpen = false;
      chatBox.classList.remove("open");
      toggleBtn.classList.remove("open");
    });

    formEl.addEventListener("submit", function (e) {
      e.preventDefault();

      var text = inputEl.value.trim();
      if (!text) return;

      inputEl.value = "";
      addBubble("user", text);
      conversation.push({ role: "user", content: text });
      sendToServer();
    });

    function sendToServer() {
      sendBtn.disabled = true;
      var thinkingBubble = addThinkingBubble();

      fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: conversation }),
      })
        .then(function (res) {
          if (!res.ok) throw new Error("bad status " + res.status);
          return res.json();
        })
        .then(function (data) {
          thinkingBubble.remove();
          var reply = data.reply || "Hmm, not sure what happened there - mind trying again?";
          addBubble("bot", reply);
          conversation.push({ role: "assistant", content: reply });
        })
        .catch(function () {
          thinkingBubble.remove();
          addBubble("bot", "Sorry - having trouble connecting right now. Try again in a bit, or reach out to your nearest branch directly.");
        })
        .finally(function () {
          sendBtn.disabled = false;
        });
    }
  });
})();
