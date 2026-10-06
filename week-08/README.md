# Week 8 — starter: Platform API opened to the mobile app

The API trusts the X-User header, has no authorization and a hard-coded secret. Python 3.10+, no installs.

    python api.py                              # terminal 1: http://127.0.0.1:8103
    python client.py maria GET /students/2/grades
    python client.py prof.stoyanova POST /grades '{"student_id": 2, "course_id": 1, "grade": 5.5}'
    python attack.py                           # 10 attacks + 5 legitimate requests
    python verify.py                           # stop your api.py first; verify starts its own (add --punch after the Punch is released)

Data is in memory and resets when api.py restarts.
Your lab guide: weeks/week-08/student-guide.md
