# Седмица 9 — начален код: Университетски асистент (само LLM)

Асистентът изпраща въпросите направо към модела. Пътят през RAG е задачата в „Изгради“. Python 3.10+, без инсталации.

    python ask.py "What do I need to pass Software Architecture?" --mode llm
    python ask.py "What do I need to pass Software Architecture?"      # RAG, след „Изгради“
    python verify.py                     # сценарии за приемане (добави --punch за Втория удар)

Моделът зад llm_client.py (границата на модела) се избира с LLM_BACKEND:
    fake    (по подразбиране) детерминиран офлайн заместител — без мрежа, без ключ
    ollama  локален Ollama (OLLAMA_MODEL, по подразбиране llama3.2)
    openai  всеки API, съвместим с OpenAI (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL)
verify.py винаги използва fake. Документите със знания са в knowledge/*.txt
Ръководство за упражнението: bg/weeks/week-09/student-guide.md

Вторият удар (punch-09.zip) се раздава в залата; дотогава `--punch` съобщава, че още не е пуснат.
