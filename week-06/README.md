# Week 6 — starter: modular monolith + an empty Catalogue Service

Monolith (students, catalogue, enrollment, reports) over data/university.db.
A separate Catalogue Service skeleton in catalog_service/ (port 8101, own catalog.db). Python 3.10+, no installs.

    python app.py list-courses | list-students | fill-report | reset
    python app.py enroll 1 2
    python catalog_service/run.py              # terminal 2: the service (one route; add the second)
    CATALOG=remote python app.py list-courses  # monolith using the service (after the Build)
    python verify.py                           # starts/stops the service itself (add --punch)

Your lab guide: weeks/week-06/student-guide.md

Stop your own server (Ctrl+C) before verify.py — it refuses to run if port 8101 is busy.
The Second Punch (punch_scenarios.py) is handed out in class at 15:50.
