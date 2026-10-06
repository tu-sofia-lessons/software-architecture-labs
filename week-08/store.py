"""In-memory university data, reset at every server start (provided)."""

STUDENTS = {
    1: {"id": 1, "name": "Maria Ivanova", "email": "maria.ivanova@tu-sofia.bg"},
    2: {"id": 2, "name": "Ivan Petrov", "email": "ivan.petrov@tu-sofia.bg"},
    3: {"id": 3, "name": "Georgi Georgiev", "email": "georgi.georgiev@tu-sofia.bg"},
    4: {"id": 4, "name": "Elena Dimitrova", "email": "elena.dimitrova@tu-sofia.bg"},
}

# teacher_login / assistants link a course to user accounts in the identity provider
COURSES = {
    1: {"id": 1, "code": "SA101", "title": "Software Architecture", "teacher": "Prof. Stoyanova",
        "capacity": 3, "teacher_login": "prof.stoyanova", "assistants": ["ta.georgieva"]},
    2: {"id": 2, "code": "AI201", "title": "Artificial Intelligence", "teacher": "Prof. Kolev",
        "capacity": 2, "teacher_login": "prof.kolev", "assistants": []},
    3: {"id": 3, "code": "DB150", "title": "Databases", "teacher": "Dr. Marinov",
        "capacity": 30, "teacher_login": "dr.marinov", "assistants": []},
    4: {"id": 4, "code": "PR102", "title": "Programming 2", "teacher": "Dr. Petkova",
        "capacity": 30, "teacher_login": "dr.petkova", "assistants": []},
}

ENROLLMENTS = {(1, 1), (2, 1), (2, 2)}                 # (student_id, course_id)
GRADES = {(1, 1): 5.50, (2, 1): 4.75, (2, 2): 4.00}    # Bulgarian scale 2.00–6.00
