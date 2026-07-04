# ARES — Adaptive Reasoning Executive System

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## What is ARES?

ARES is a modular desktop AI system designed to function as a **strategic advisor**. It analyzes situations, identifies optimal paths, and presents structured recommendations — with the calm precision of a tactical operations system.

It is **not** a chatbot. It does not roleplay. It does not use emoji.

### Core Traits

- **Analytical** — Decomposes problems, evaluates trade-offs, ranks options
- **Concise** — Every word serves a purpose
- **Confident** — States confidence levels when uncertainty exists
- **Modular** — Swap LLM providers with a single config change
- **Private** — Runs locally as a native desktop application

---

## Quick Start

### Prerequisites

- Python 3.11+
- A [DeepSeek API key](https://platform.deepseek.com/)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ARES.git
cd ARES

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your DeepSeek API key
```

### Launch

```bash
python main.py
```

A native desktop window will open. Start typing.

---

## Configuration

### API Key (`.env`)

Sensitive values go in `.env` (never committed to git):

```env
ARES_API_KEY=sk-your-deepseek-key-here
```

### Settings (`config.yaml`)

Non-sensitive settings:

```yaml
llm:
  provider: deepseek
  model: deepseek-v4-pro         # or deepseek-v4-flash
  max_tokens: 2048
  temperature: 0.7
  streaming: true

personality:
  directory: app/personality

memory:
  max_conversation_turns: 20

ui:
  title: "ARES"
  width: 900
  height: 700
```

### Environment Variable Overrides

Any config value can be overridden via environment variables:

| Variable | Description |
|---|---|
| `ARES_API_KEY` | LLM API key |
| `ARES_LLM_PROVIDER` | Provider name (`deepseek`) |
| `ARES_LLM_MODEL` | Model identifier |

Priority: `env vars` > `.env` > `config.yaml` > `defaults`

---

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│  pywebview (Native Window)      │
│  HTML/CSS/JS Frontend           │
│         │                       │
│         ▼                       │
│  AresAPI (Python↔JS Bridge)     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Orchestrator                   │
│  (Coordinates all modules)      │
│         │                       │
│    ┌────┼────┬──────────┐       │
│    ▼    ▼    ▼          ▼       │
│  Pers. Prompt Memory   LLM     │
│  Engine Builder Manager Provider│
└─────────────────────────────────┘
```

The Orchestrator contains **no AI logic** — it only coordinates. Every module is independently replaceable.

### Key Design Principles

- **LLM is replaceable.** Swap providers by changing one config value.
- **Personality is configurable.** Edit markdown files in `app/personality/`.
- **Observe, not control.** ARES reads system state but never modifies it.
- **Modular stubs.** Future modules (voice, vision, tools) have interfaces defined but unplugged.

---

## Project Structure

```
ARES/
├── main.py                          # Entry point
├── config.yaml                      # Non-sensitive configuration
├── .env                             # API keys (git-ignored)
├── .env.example                     # Template for .env
├── requirements.txt                 # Python dependencies
├── app/
│   ├── core/
│   │   ├── orchestrator.py          # Central coordinator
│   │   └── prompt_builder.py        # Assembles LLM prompts
│   ├── llm/
│   │   ├── base.py                  # Abstract provider interface
│   │   └── providers/
│   │       └── deepseek.py          # DeepSeek API (OpenAI-compatible)
│   ├── personality/
│   │   ├── engine.py                # Loads personality markdown files
│   │   ├── communication.md         # How ARES speaks
│   │   ├── behavior.md              # How ARES acts
│   │   ├── reasoning.md             # How ARES thinks
│   │   └── ethics.md                # Boundaries and integrity
│   ├── memory/
│   │   └── manager.py               # Conversation history (sliding window)
│   ├── ui/
│   │   ├── window.py                # pywebview native window
│   │   ├── api.py                   # Python↔JS bridge
│   │   └── web/
│   │       ├── index.html           # UI structure
│   │       ├── styles.css           # Dark theme
│   │       └── app.js               # Frontend logic
│   ├── voice/tts.py                 # TTS stub (future: Piper TTS)
│   ├── speech/stt.py                # STT stub (future: faster-whisper)
│   ├── vision/capture.py            # Vision stub (future: screenshots)
│   └── tools/base.py                # Tool stub (future: filesystem, etc.)
├── logs/                            # Runtime logs (git-ignored)
└── tests/                           # Test directory
```

---

## Personality

ARES personality is defined in editable markdown files under `app/personality/`. You can modify these without touching any code:

| File | Controls |
|---|---|
| `communication.md` | Tone, formatting rules, prohibitions |
| `behavior.md` | Response framework, operating principles |
| `reasoning.md` | Analytical approach, decision support |
| `ethics.md` | Transparency, integrity, boundaries |

Changes take effect on next launch (or when personality cache is refreshed).

---

## Roadmap

### Phase 1 ✅ (Current)
- [x] Text chat with DeepSeek API (streaming)
- [x] Personality engine (markdown configuration)
- [x] Native desktop UI (dark theme)
- [x] Conversation history with context window
- [x] Configuration system with `.env` support
- [x] Logging

### Phase 2 (Planned)
- [ ] Voice input (faster-whisper STT)
- [ ] Voice output (Piper TTS with custom voice)
- [ ] RAG memory system (ChromaDB)
- [ ] Screenshot analysis (vision module)
- [ ] Desktop awareness (system info)
- [ ] Basic tools (filesystem, clipboard, time)

### Phase 3 (Future)
- [ ] Project management
- [ ] Daily journal generation
- [ ] Plugin system
- [ ] Local fallback LLM (Ollama)

---

## License

MIT

---

