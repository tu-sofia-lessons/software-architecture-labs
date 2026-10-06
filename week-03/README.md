# Week 3 — starter: Course Materials, local store (remote store not built yet)

Python 3.10+, no installs. Materials live in local_materials/; Faculty IT's server serves server_files/.

    python cli.py list-students
    python cli.py materials list 1 | get 1 lecture01.txt | put 1 some_file.txt
    python file_server.py                       # terminal 2: Faculty IT's file server on :8102
    python peek_http.py /courses/1/materials    # see the raw HTTP request/response bytes
    MATERIALS_BACKEND=remote python cli.py materials list 1      (Windows cmd: set "MATERIALS_BACKEND=remote")
    python verify.py                            # starts its own server (stop yours first); --punch after 15:50

Your lab guide: weeks/week-03/student-guide.md
