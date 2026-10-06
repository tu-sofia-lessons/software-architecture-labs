# Седмица 5 — начален код: записване с директни странични ефекти

EnrollmentService извиква директно пощата, одитния дневник и статистиката.
Python 3.10+, без инсталации (Windows: `py -3` вместо `python`).

    python app.py enroll 1 3 2 3
    MAIL_DOWN=1 python app.py enroll 1 3      # PowerShell: $env:MAIL_DOWN="1"; py -3 app.py enroll 1 3
    python verify.py                          # редовете REQ се оценяват, [path] са насоки

Предоставена инфраструктура: eventbus.py (синхронна/асинхронна шина в същия процес). Данни: data.py.
Втори удар: асистентът пуска punch-05.zip в 15:50; разархивирай го тук и пусни `python verify.py --punch`.
Ръководството за упражнението: bg/weeks/week-05/student-guide.md
