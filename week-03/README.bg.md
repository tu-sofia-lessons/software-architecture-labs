# Седмица 3 — начален код: учебни материали, локално хранилище (отдалеченото хранилище още не е изградено)

Python 3.10+, без инсталиране на пакети. Материалите са в local_materials/; сървърът на ИТ отдела обслужва server_files/.

    python cli.py list-students
    python cli.py materials list 1 | get 1 lecture01.txt | put 1 some_file.txt
    python file_server.py                       # terminal 2: Faculty IT's file server on :8102
    python peek_http.py /courses/1/materials    # see the raw HTTP request/response bytes
    MATERIALS_BACKEND=remote python cli.py materials list 1      (Windows cmd: set "MATERIALS_BACKEND=remote")
    python verify.py                            # пуска собствен сървър (първо спри твоя); --punch след 15:50

Ръководство за упражнението: bg/weeks/week-03/student-guide.md
