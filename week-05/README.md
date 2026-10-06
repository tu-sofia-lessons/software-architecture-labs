# Week 5 — starter: Enrollment with direct side effects

EnrollmentService calls the mailer, the audit log and statistics directly.
Python 3.10+, no installs (Windows: `py -3` instead of `python`).

    python app.py enroll 1 3 2 3
    MAIL_DOWN=1 python app.py enroll 1 3      # PowerShell: $env:MAIL_DOWN="1"; py -3 app.py enroll 1 3
    python verify.py                          # REQ lines are graded, [path] lines are hints

Provided infrastructure: eventbus.py (sync/async in-process bus). Data: data.py (seed).
Second Punch: the assistant releases punch-05.zip at 15:50; unzip it here, then `python verify.py --punch`.
Your lab guide: weeks/week-05/student-guide.md
