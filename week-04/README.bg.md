# Седмица 4 — начален код: внос на студенти (една голяма функция)

Инструмент за внос на Учебния отдел. Вносът от приема работи чрез една стара функция; Erasmus още не се поддържа.
Python 3.10+, без инсталиране на пакети (Windows: `py -3` вместо `python`).

    python import_cli.py admissions
    python import_cli.py erasmus
    python verify.py                     # редовете REQ се оценяват, [path] са насоки

Файлове: data/*.csv (източници), importer/pipeline.py (предоставен изпълнител), importer/legacy_import.py (голямата функция).
Втори удар: асистентът пуска punch-04.zip в 15:50; разархивирай го тук и пусни `python verify.py --punch`.
Ръководство за упражнението: bg/weeks/week-04/student-guide.md
