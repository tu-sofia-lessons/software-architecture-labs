# Week 9 — starter: University Assistant (LLM only)

The assistant sends questions straight to the model. The RAG path is the Build. Python 3.10+, no installs.

    python ask.py "What do I need to pass Software Architecture?" --mode llm
    python ask.py "What do I need to pass Software Architecture?"      # RAG, after the Build
    python verify.py                     # acceptance scenarios (add --punch for the Second Punch)

Model backend (llm_client.py, the model boundary) is chosen with LLM_BACKEND:
    fake    (default) deterministic offline stand-in — no network, no key
    ollama  local Ollama (OLLAMA_MODEL, default llama3.2)
    openai  any OpenAI-compatible API (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL)
verify.py always uses the fake. Knowledge documents: knowledge/*.txt
Your lab guide: weeks/week-09/student-guide.md

The Second Punch (punch-09.zip) is handed out in class; before that, `--punch` says it is not released yet.
