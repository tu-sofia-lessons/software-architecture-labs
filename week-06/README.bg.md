# Седмица 6 — начален код: модулен монолит + празна Услуга на Каталога

Монолит (студенти, каталог, записване, справки) върху data/university.db.
Отделна обвивка на Услугата на Каталога в catalog_service/ (порт 8101, собствен catalog.db). Python 3.10+, без инсталации.

    python app.py list-courses | list-students | fill-report | reset
    python app.py enroll 1 2
    python catalog_service/run.py              # terminal 2: the service (one route; add the second)
    CATALOG=remote python app.py list-courses  # monolith using the service (after the Build)
    python verify.py                           # starts/stops the service itself (add --punch)

Ръководството ти за упражнението: bg/weeks/week-06/student-guide.md

Спри своя сървър (Ctrl+C) преди verify.py — отказва да работи, ако порт 8101 е зает.
Вторият удар (punch_scenarios.py) се раздава в залата в 15:50.
