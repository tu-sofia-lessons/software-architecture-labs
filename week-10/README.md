# Week 10 — starter: University Assistant agent (no guard)

The agent loop, tools and platform work. guard.py lets every proposed action through. Python 3.10+, no installs.

    python chat.py --user maria "Which of my courses still have seats?"
    python chat.py --user maria "Enroll me in Databases"
    python chat.py --user maria "Enroll Ivan in Databases"      # should that work?
    python verify.py                     # acceptance scenarios (add --punch for the Second Punch)

Users: maria, ivan, elena (students), registrar (admin). Data is in memory, reset on every run.
Model backend (llm_client.py) via LLM_BACKEND: fake (default, deterministic, offline),
ollama (OLLAMA_MODEL), openai (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL). verify.py always uses the fake.
Your lab guide: weeks/week-10/student-guide.md (Part B: the Solution Architecture Challenge)

The Second Punch (punch-10.zip) is handed out in class; before that, `--punch` says it is not released yet.
