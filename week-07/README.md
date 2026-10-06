# Week 7 — starter: monolith + a slow, flaky Catalogue Service

The Week 6 architecture (monolith → HTTP → Catalogue Service on port 8101), plus chaos flags,
a load generator and logging helpers. Python 3.10+, no installs.

    python catalog_service/run.py --delay 3            # terminal 2 (also: --fail-rate 0.5, --seed 7)
    python app.py browse | enroll 1 1 | list-students
    OBS_LOG=client.log python app.py browse           # structured logs to a file
    python loadgen.py --users 50 [--naive]            # needs the service running
    python verify.py                                  # starts/stops the service itself (~40 s, add --punch)

Your lab guide: weeks/week-07/student-guide.md

Stop your own server (Ctrl+C) before verify.py — it refuses to run if port 8101 is busy.
The Second Punch (punch_scenarios.py) is handed out in class at 15:50.
