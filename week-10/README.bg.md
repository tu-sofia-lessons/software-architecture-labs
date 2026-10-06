# Седмица 10 — начален код: агент на Университетския асистент (без пазач)

Цикълът на агента, инструментите и платформата работят. guard.py пропуска всяко предложено действие. Python 3.10+, без инсталации.

    python chat.py --user maria "Which of my courses still have seats?"
    python chat.py --user maria "Enroll me in Databases"
    python chat.py --user maria "Enroll Ivan in Databases"      # трябва ли това да работи?
    python verify.py                     # сценарии за приемане (добави --punch за Втория удар)

Потребители: maria, ivan, elena (студенти), registrar (администратор). Данните са в паметта и се нулират при всяко стартиране.
Моделът зад llm_client.py се избира с LLM_BACKEND: fake (по подразбиране, детерминиран, офлайн),
ollama (OLLAMA_MODEL), openai (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL). verify.py винаги използва fake.
Ръководство за упражнението: bg/weeks/week-10/student-guide.md (Част Б: Предизвикателство по архитектура на решения)

Вторият удар (punch-10.zip) се раздава в залата; дотогава `--punch` съобщава, че още не е пуснат.
