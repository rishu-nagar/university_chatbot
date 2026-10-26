// chat.js - Chat interface logic
// =========================================================
// Handles message sending, receiving, chat history,
// sidebar, suggested prompts, and UI state management.
// =========================================================

(function () {
    "use strict";

    // ── DOM Elements ──────────────────────────────────
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const welcomeScreen     = $("#welcome-screen");
    const messagesList      = $("#messages-list");
    const composerForm      = $("#composer-form");
    const messageInput      = $("#message-input");
    const sendBtn           = $("#send-btn");
    const charCount         = $("#char-count");
    const chatContainer     = $("#chat-container");
    const scrollBottomBtn   = $("#scroll-bottom-btn");
    const sidebar           = $("#sidebar");
    const sidebarOverlay    = $("#sidebar-overlay");
    const sidebarToggle     = $("#sidebar-toggle");
    const mobileMenuBtn     = $("#mobile-menu-btn");
    const newChatBtn        = $("#new-chat-btn");
    const mobileNewChat     = $("#mobile-new-chat");
    const categoryList      = $("#category-list");
    const historyList       = $("#history-list");
    const statusDot         = $("#status-dot");
    const statusText        = $("#status-text");
    const toastContainer    = $("#toast-container");
    const promptCards       = $$(".prompt-card");

    // ── State ─────────────────────────────────────────
    let isLoading = false;
    let chatMessages = [];  // Local copy of messages
    let chatHistories = []; // Saved chat sessions

    // ── Initialization ────────────────────────────────
    function init() {
        loadChatHistories();
        renderHistoryList();
        fetchCategories();
        checkHealth();
        bindEvents();
        autoResizeTextarea();
    }

    // ── Event Bindings ────────────────────────────────
    function bindEvents() {
        // Composer
        composerForm.addEventListener("submit", handleSubmit);
        messageInput.addEventListener("input", handleInputChange);
        messageInput.addEventListener("keydown", handleKeyDown);

        // Suggested prompts
        promptCards.forEach((card) => {
            card.addEventListener("click", () => {
                const prompt = card.getAttribute("data-prompt");
                if (prompt) sendMessage(prompt);
            });
        });

        // New chat
        newChatBtn.addEventListener("click", handleNewChat);
        if (mobileNewChat) mobileNewChat.addEventListener("click", handleNewChat);

        // Sidebar toggles
        if (mobileMenuBtn) mobileMenuBtn.addEventListener("click", toggleSidebar);
        if (sidebarToggle) sidebarToggle.addEventListener("click", closeSidebar);
        if (sidebarOverlay) sidebarOverlay.addEventListener("click", closeSidebar);

        // Scroll-to-bottom
        chatContainer.addEventListener("scroll", handleScroll);
        scrollBottomBtn.addEventListener("click", scrollToBottom);
    }

    // ── Composer Handlers ─────────────────────────────
    function handleInputChange() {
        const len = messageInput.value.length;
        charCount.textContent = `${len} / 2000`;
        charCount.className = "char-count" +
            (len > 1800 ? " danger" : len > 1500 ? " warning" : "");

        // Toggle send button
        const hasContent = messageInput.value.trim().length > 0;
        sendBtn.classList.toggle("active", hasContent && !isLoading);

        autoResizeTextarea();
    }

    function handleKeyDown(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (messageInput.value.trim() && !isLoading) {
                handleSubmit(e);
            }
        }
    }

    function handleSubmit(e) {
        e.preventDefault();
        const text = messageInput.value.trim();
        if (!text || isLoading) return;
        sendMessage(text);
    }

    function autoResizeTextarea() {
        messageInput.style.height = "auto";
        messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + "px";
    }

    // ── Send Message ──────────────────────────────────
    async function sendMessage(text) {
        if (isLoading) return;
        isLoading = true;

        // Show messages view, hide welcome
        showChatView();

        // Add user message
        addMessage("user", text);

        // Clear input
        messageInput.value = "";
        handleInputChange();

        // Show typing indicator
        const typingEl = addTypingIndicator();
        scrollToBottom();

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text }),
            });

            const data = await response.json();

            // Remove typing indicator
            removeTypingIndicator(typingEl);

            if (data.success) {
                addMessage("bot", data.response, data.sources, data.timestamp);
            } else {
                addMessage("bot", `⚠️ ${data.error || "Something went wrong. Please try again."}`);
            }
        } catch (err) {
            removeTypingIndicator(typingEl);
            addMessage("bot", "⚠️ Unable to reach the server. Please check your connection and try again.");
            console.error("Chat error:", err);
        }

        isLoading = false;
        scrollToBottom();
        saveChatHistory();
    }

    // ── Message Rendering ─────────────────────────────
    function addMessage(role, content, sources, timestamp) {
        chatMessages.push({ role, content, sources, timestamp });

        const msgEl = document.createElement("div");
        msgEl.className = `message ${role === "user" ? "user-message" : "bot-message"}`;

        const avatarEl = document.createElement("div");
        avatarEl.className = "message-avatar";
        avatarEl.textContent = role === "user" ? "You" : "AI";
        avatarEl.setAttribute("aria-hidden", "true");

        const bubbleEl = document.createElement("div");
        bubbleEl.className = "message-bubble";

        if (role === "bot") {
            bubbleEl.innerHTML = renderMarkdown(content);
        } else {
            bubbleEl.textContent = content;
        }

        // Sources chips
        if (sources && sources.length > 0) {
            const sourcesEl = document.createElement("div");
            sourcesEl.className = "message-sources";
            sources.forEach((s) => {
                const chip = document.createElement("span");
                chip.className = "source-chip";
                chip.textContent = s.category;
                sourcesEl.appendChild(chip);
            });
            bubbleEl.appendChild(sourcesEl);
        }

        // Timestamp meta
        if (timestamp) {
            const metaEl = document.createElement("div");
            metaEl.className = "message-meta";
            metaEl.textContent = timestamp;
            bubbleEl.appendChild(metaEl);
        }

        msgEl.appendChild(avatarEl);
        msgEl.appendChild(bubbleEl);
        messagesList.appendChild(msgEl);

        scrollToBottom();
    }

    function addTypingIndicator() {
        const msgEl = document.createElement("div");
        msgEl.className = "message bot-message typing-message";
        msgEl.id = "typing-indicator";

        const avatarEl = document.createElement("div");
        avatarEl.className = "message-avatar";
        avatarEl.textContent = "AI";

        const bubbleEl = document.createElement("div");
        bubbleEl.className = "message-bubble typing-indicator";
        bubbleEl.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;

        msgEl.appendChild(avatarEl);
        msgEl.appendChild(bubbleEl);
        messagesList.appendChild(msgEl);

        return msgEl;
    }

    function removeTypingIndicator(el) {
        if (el && el.parentNode) {
            el.parentNode.removeChild(el);
        }
    }

    // ── Markdown Renderer ─────────────────────────────
    function renderMarkdown(text) {
        if (!text) return "";
        let html = escapeHtml(text);

        // Horizontal rules
        html = html.replace(/^---$/gm, "<hr>");

        // Headings
        html = html.replace(/^###\s+(.+)$/gm, "<h4>$1</h4>");
        html = html.replace(/^##\s+(.+)$/gm, "<h3>$1</h3>");
        html = html.replace(/^#\s+(.+)$/gm, "<h3>$1</h3>");

        // Bold and Italic
        html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
        // Inline code
        html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

        // Ordered lists: use temporary tag <oli> to separate from unordered <li>
        html = html.replace(/^\d+\.\s+(.+)$/gm, "<oli>$1</oli>");
        html = html.replace(/((?:<oli>.*<\/oli>\n?)+)/g, "<ol>$1</ol>");
        html = html.replace(/<oli>/g, "<li>").replace(/<\/oli>/g, "</li>");

        // Unordered lists (• or - or *)
        html = html.replace(/^[•\-\*]\s+(.+)$/gm, "<li>$1</li>");
        html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>");

        // Paragraphs: split by double newlines, but protect block tags
        html = html.replace(/\n\n+/g, "\n\n");
        const blocks = html.split("\n\n");
        html = blocks
            .map((b) => {
                b = b.trim();
                if (!b) return "";
                if (b.startsWith("<ul") || b.startsWith("<ol") || b.startsWith("<h3") || b.startsWith("<h4") || b.startsWith("<hr")) {
                    return b;
                }
                return "<p>" + b.replace(/\n/g, "<br>") + "</p>";
            })
            .filter(Boolean)
            .join("");

        // Clean up any stray tags
        html = html.replace(/<p>\s*<\/p>/g, "");
        return html;
    }

    function escapeHtml(text) {
        const el = document.createElement("div");
        el.textContent = text;
        return el.innerHTML;
    }

    // ── UI State ──────────────────────────────────────
    function showChatView() {
        welcomeScreen.style.display = "none";
        messagesList.classList.add("active");
    }

    function showWelcomeView() {
        welcomeScreen.style.display = "";
        messagesList.classList.remove("active");
        messagesList.innerHTML = "";
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
    }

    function handleScroll() {
        const { scrollTop, scrollHeight, clientHeight } = chatContainer;
        const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
        scrollBottomBtn.style.display = distanceFromBottom > 200 ? "flex" : "none";
    }

    // ── Sidebar ───────────────────────────────────────
    function toggleSidebar() {
        sidebar.classList.toggle("open");
        sidebarOverlay.classList.toggle("open");
    }

    function closeSidebar() {
        sidebar.classList.remove("open");
        sidebarOverlay.classList.remove("open");
    }

    // ── New Chat ──────────────────────────────────────
    function handleNewChat() {
        // Save current chat before starting a new one
        if (chatMessages.length > 0) {
            saveChatHistory();
        }
        chatMessages = [];
        showWelcomeView();
        closeSidebar();

        // Clear server-side session history
        fetch("/api/clear", { method: "POST" }).catch(() => {});

        showToast("New conversation started", "success");
    }

    // ── Chat History Persistence (localStorage) ──────
    function saveChatHistory() {
        if (chatMessages.length === 0) return;

        // Summarize with the first user message
        const firstUserMsg = chatMessages.find((m) => m.role === "user");
        const title = firstUserMsg
            ? firstUserMsg.content.substring(0, 60) + (firstUserMsg.content.length > 60 ? "…" : "")
            : "New Conversation";

        // Check if we're updating an existing session or creating new
        const existingIdx = chatHistories.findIndex(
            (h) => h.id === currentSessionId
        );
        const session = {
            id: currentSessionId || generateId(),
            title,
            messages: chatMessages.slice(),
            timestamp: new Date().toISOString(),
        };
        currentSessionId = session.id;

        if (existingIdx >= 0) {
            chatHistories[existingIdx] = session;
        } else {
            chatHistories.unshift(session);
        }

        // Keep max 20 sessions
        chatHistories = chatHistories.slice(0, 20);

        try {
            localStorage.setItem("aurora_chat_histories", JSON.stringify(chatHistories));
        } catch (e) {
            console.warn("Could not save chat history to localStorage:", e);
        }

        renderHistoryList();
    }

    let currentSessionId = null;

    function loadChatHistories() {
        try {
            const stored = localStorage.getItem("aurora_chat_histories");
            chatHistories = stored ? JSON.parse(stored) : [];
        } catch {
            chatHistories = [];
        }
        currentSessionId = generateId();
    }

    function renderHistoryList() {
        if (!historyList) return;

        if (chatHistories.length === 0) {
            historyList.innerHTML = '<div class="history-empty"><span>No conversations yet</span></div>';
            return;
        }

        historyList.innerHTML = "";
        chatHistories.forEach((session) => {
            const btn = document.createElement("button");
            btn.className = "history-item";
            btn.innerHTML = `
                <svg class="history-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M2 3.5H12M2 7H9M2 10.5H12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                </svg>
                <span>${escapeHtml(session.title)}</span>
            `;
            btn.addEventListener("click", () => loadSession(session));
            historyList.appendChild(btn);
        });
    }

    function loadSession(session) {
        // Save current chat first
        if (chatMessages.length > 0 && currentSessionId !== session.id) {
            saveChatHistory();
        }

        currentSessionId = session.id;
        chatMessages = [];
        messagesList.innerHTML = "";
        showChatView();

        // Re-render all messages
        session.messages.forEach((msg) => {
            addMessage(msg.role, msg.content, msg.sources, msg.timestamp);
        });

        closeSidebar();

        // Clear server-side session so new messages don't mix
        fetch("/api/clear", { method: "POST" }).catch(() => {});
    }

    // ── Categories ────────────────────────────────────
    async function fetchCategories() {
        try {
            const res = await fetch("/api/categories");
            const data = await res.json();
            if (data.success && data.categories) {
                renderCategories(data.categories);
            }
        } catch (err) {
            console.warn("Could not fetch categories:", err);
        }
    }

    function renderCategories(categories) {
        if (!categoryList) return;
        categoryList.innerHTML = "";
        categories.forEach((cat) => {
            const btn = document.createElement("button");
            btn.className = "category-item";
            btn.innerHTML = `<span class="cat-icon">${cat.icon}</span><span>${escapeHtml(cat.name)}</span>`;
            btn.addEventListener("click", () => {
                sendMessage(`Tell me about ${cat.name}`);
                closeSidebar();
            });
            categoryList.appendChild(btn);
        });
    }

    // ── Health Check ──────────────────────────────────
    async function checkHealth() {
        try {
            const res = await fetch("/api/health");
            const data = await res.json();
            if (data.ai_available) {
                statusDot.className = "status-dot online";
                statusText.textContent = "AI powered";
            } else {
                statusDot.className = "status-dot offline";
                statusText.textContent = "FAQ-only mode";
            }
        } catch {
            statusDot.className = "status-dot offline";
            statusText.textContent = "Offline";
        }
    }

    // ── Toast Notifications ───────────────────────────
    function showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add("removing");
            setTimeout(() => toast.remove(), 250);
        }, 3000);
    }

    // ── Utilities ─────────────────────────────────────
    function generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substring(2, 8);
    }

    // ── Boot ──────────────────────────────────────────
    init();
})();
