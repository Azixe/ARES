/**
 * ARES — Frontend Application Logic
 * Handles UI interactions, message rendering, and Python API communication.
 */

(function () {
    'use strict';

    // === DOM ELEMENTS ===
    const elements = {
        chatArea: document.getElementById('chat-area'),
        messages: document.getElementById('messages'),
        welcome: document.getElementById('welcome'),
        input: document.getElementById('message-input'),
        sendBtn: document.getElementById('btn-send'),
        clearBtn: document.getElementById('btn-clear'),
        statusDot: document.getElementById('status-dot'),
        statusText: document.getElementById('status-text'),
        modelInfo: document.getElementById('model-info'),
        turnCount: document.getElementById('turn-count'),
    };

    // === STATE ===
    let state = {
        isProcessing: false,
        currentResponseEl: null,
        currentResponseText: '',
        messageCount: 0,
    };

    // === MARKDOWN RENDERER (lightweight) ===
    function renderMarkdown(text) {
        if (!text) return '';

        let html = text;

        // Escape HTML entities first
        html = html
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Code blocks (``` ... ```) — must be processed before inline patterns
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function (match, lang, code) {
            return '<pre><code class="language-' + (lang || 'text') + '">' + code.trim() + '</code></pre>';
        });

        // Inline code (` ... `)
        html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');

        // Headers
        html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

        // Bold & Italic
        html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Blockquotes
        html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

        // Horizontal rules
        html = html.replace(/^---$/gm, '<hr>');

        // Unordered lists
        html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
        html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

        // Ordered lists
        html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

        // Tables (basic)
        html = html.replace(/^\|(.+)\|$/gm, function (match, content) {
            const cells = content.split('|').map(c => c.trim());
            // Check if it's a separator row
            if (cells.every(c => /^[\-:]+$/.test(c))) {
                return '<!-- table-sep -->';
            }
            const isHeader = false; // We'll handle headers via CSS
            const tag = 'td';
            const row = cells.map(c => '<' + tag + '>' + c + '</' + tag + '>').join('');
            return '<tr>' + row + '</tr>';
        });
        html = html.replace(/<!-- table-sep -->/g, '');
        html = html.replace(/((?:<tr>.*<\/tr>\n?)+)/g, '<table>$1</table>');

        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        // Paragraphs — wrap loose text lines
        html = html.replace(/^(?!<[a-z]|$)(.+)$/gm, '<p>$1</p>');

        // Clean up empty paragraphs and consecutive breaks
        html = html.replace(/<p><\/p>/g, '');
        html = html.replace(/\n{3,}/g, '\n\n');

        return html.trim();
    }

    // === MESSAGE RENDERING ===
    function addMessage(role, content, isHtml) {
        // Hide welcome screen on first message
        if (elements.welcome && !elements.welcome.classList.contains('hidden')) {
            elements.welcome.classList.add('hidden');
        }

        const messageEl = document.createElement('div');
        messageEl.className = 'message ' + role;

        const label = document.createElement('div');
        label.className = 'message-label';
        label.textContent = role === 'user' ? 'YOU' : 'ARES';

        const contentEl = document.createElement('div');
        contentEl.className = 'message-content';

        if (isHtml) {
            contentEl.innerHTML = content;
        } else if (role === 'user') {
            contentEl.textContent = content;
        } else {
            contentEl.innerHTML = renderMarkdown(content);
        }

        messageEl.appendChild(label);
        messageEl.appendChild(contentEl);
        elements.messages.appendChild(messageEl);

        state.messageCount++;
        scrollToBottom();

        return contentEl;
    }

    function addErrorMessage(text) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message error';

        const label = document.createElement('div');
        label.className = 'message-label';
        label.textContent = 'SYSTEM';
        label.style.color = 'var(--error)';

        const contentEl = document.createElement('div');
        contentEl.className = 'message-content';
        contentEl.textContent = text;

        messageEl.appendChild(label);
        messageEl.appendChild(contentEl);
        elements.messages.appendChild(messageEl);

        scrollToBottom();
    }

    function scrollToBottom() {
        requestAnimationFrame(function () {
            elements.chatArea.scrollTop = elements.chatArea.scrollHeight;
        });
    }

    // === STATUS MANAGEMENT ===
    function setStatus(status) {
        const dot = elements.statusDot;
        const text = elements.statusText;

        // Remove all status classes
        dot.className = 'status-dot';

        switch (status) {
            case 'idle':
                dot.classList.add('idle');
                text.textContent = 'Ready';
                break;
            case 'thinking':
                dot.classList.add('thinking');
                text.textContent = 'Thinking';
                break;
            case 'speaking':
                dot.classList.add('speaking');
                text.textContent = 'Speaking';
                break;
            case 'error':
                dot.classList.add('error');
                text.textContent = 'Error';
                break;
            default:
                text.textContent = status;
        }
    }

    // === INPUT HANDLING ===
    function autoResizeInput() {
        const input = elements.input;
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 150) + 'px';
    }

    function updateSendButton() {
        elements.sendBtn.disabled = !elements.input.value.trim() || state.isProcessing;
    }

    function sendMessage() {
        const text = elements.input.value.trim();
        if (!text || state.isProcessing) return;

        state.isProcessing = true;
        updateSendButton();

        // Display user message immediately
        addMessage('user', text);

        // Clear input
        elements.input.value = '';
        autoResizeInput();

        // Send to Python backend
        if (window.pywebview && window.pywebview.api) {
            pywebview.api.send_message(text);
        } else {
            addErrorMessage('Backend not connected. pywebview API unavailable.');
            state.isProcessing = false;
            updateSendButton();
        }
    }

    // === EVENT LISTENERS ===
    elements.input.addEventListener('input', function () {
        autoResizeInput();
        updateSendButton();
    });

    elements.input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    elements.sendBtn.addEventListener('click', sendMessage);

    elements.clearBtn.addEventListener('click', function () {
        if (state.isProcessing) return;
        if (state.messageCount === 0) return;

        if (window.pywebview && window.pywebview.api) {
            pywebview.api.clear_history();
        }
    });

    // === PYWEBVIEW API — Called from Python ===
    window.ares = {
        updateStatus: function (status) {
            setStatus(status);
        },

        startResponse: function () {
            // Create a new assistant message container with typing indicator
            const contentEl = addMessage('assistant', 
                '<div class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>',
                true
            );
            state.currentResponseEl = contentEl;
            state.currentResponseText = '';
        },

        appendChunk: function (chunk) {
            if (!state.currentResponseEl) return;

            state.currentResponseText += chunk;

            // Render accumulated text as markdown with streaming cursor
            state.currentResponseEl.innerHTML = renderMarkdown(state.currentResponseText);
            state.currentResponseEl.classList.add('streaming-cursor');
            scrollToBottom();
        },

        finalizeResponse: function () {
            if (state.currentResponseEl) {
                // Final render without cursor
                state.currentResponseEl.innerHTML = renderMarkdown(state.currentResponseText);
                state.currentResponseEl.classList.remove('streaming-cursor');
                state.currentResponseEl = null;
                state.currentResponseText = '';
            }

            state.isProcessing = false;
            updateSendButton();
            updateTurnCount();
            elements.input.focus();
        },

        showError: function (message) {
            // Remove typing indicator if present
            if (state.currentResponseEl) {
                state.currentResponseEl.closest('.message').remove();
                state.currentResponseEl = null;
                state.currentResponseText = '';
            }

            addErrorMessage(message);
            state.isProcessing = false;
            updateSendButton();
            setStatus('error');

            // Recover to idle after 3 seconds
            setTimeout(function () { setStatus('idle'); }, 3000);
        },

        clearChat: function () {
            elements.messages.innerHTML = '';
            state.messageCount = 0;
            state.currentResponseEl = null;
            state.currentResponseText = '';

            // Show welcome screen again
            if (elements.welcome) {
                elements.welcome.classList.remove('hidden');
            }

            updateTurnCount();
        },
    };

    // === UTILITY ===
    function updateTurnCount() {
        if (window.pywebview && window.pywebview.api) {
            pywebview.api.get_status().then(function (status) {
                if (status && typeof status.conversation_turns !== 'undefined') {
                    elements.turnCount.textContent = status.conversation_turns + ' turns';
                }
            });
        }
    }

    function initializeUI() {
        setStatus('idle');
        elements.input.focus();

        // Load config info
        if (window.pywebview && window.pywebview.api) {
            pywebview.api.get_config_display().then(function (config) {
                if (config) {
                    elements.modelInfo.textContent = config.model || '—';
                    if (!config.has_key) {
                        addErrorMessage(
                            'No API key configured. Add your DeepSeek API key to config.yaml ' +
                            'or set the ARES_API_KEY environment variable.'
                        );
                    }
                }
            });
        }
    }

    // === INITIALIZATION ===
    // Wait for pywebview to be ready
    window.addEventListener('pywebviewready', function () {
        initializeUI();
    });

    // Fallback: if pywebview is already ready
    if (window.pywebview && window.pywebview.api) {
        initializeUI();
    }

    // Focus input when window gains focus
    window.addEventListener('focus', function () {
        if (!state.isProcessing) {
            elements.input.focus();
        }
    });

})();
