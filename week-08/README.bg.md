# Седмица 8 — начален код: API-то на платформата, отворено към мобилното приложение

API-то се доверява на заглавката X-User, няма оторизация и тайната е записана в кода. Python 3.10+, без инсталации.

    python api.py                              # terminal 1: http://127.0.0.1:8103
    python client.py maria GET /students/2/grades
    python client.py prof.stoyanova POST /grades '{"student_id": 2, "course_id": 1, "grade": 5.5}'
    python attack.py                           # 10 attacks + 5 legitimate requests
    python verify.py                           # stop your api.py first; verify starts its own (add --punch after the Punch is released)

Данните са в паметта и се нулират при рестартиране на api.py.
Ръководството ти за упражнението: bg/weeks/week-08/student-guide.md
