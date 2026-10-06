# Седмица 7 — начален код: монолит + бавна, нестабилна услуга Каталог

Архитектурата от Седмица 6 (монолит → HTTP → услуга Каталог на порт 8101), плюс флагове за хаос,
генератор на натоварване и помощни функции за журнала. Python 3.10+, без инсталации.

    python catalog_service/run.py --delay 3            # terminal 2 (also: --fail-rate 0.5, --seed 7)
    python app.py browse | enroll 1 1 | list-students
    OBS_LOG=client.log python app.py browse           # structured logs to a file
    python loadgen.py --users 50 [--naive]            # needs the service running
    python verify.py                                  # starts/stops the service itself (~40 s, add --punch)

Ръководството ти за упражнението: bg/weeks/week-07/student-guide.md

Спри своя сървър (Ctrl+C) преди verify.py — отказва да работи, ако порт 8101 е зает.
Вторият удар (punch_scenarios.py) се раздава в залата в 15:50.
