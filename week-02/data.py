"""In-memory university data (provided — stands in for the Week 1 modules and database)."""

STUDENTS = [
    {"id": 1, "name": "Maria Ivanova", "email": "maria.ivanova@tu-sofia.bg"},
    {"id": 2, "name": "Ivan Petrov", "email": "ivan.petrov@tu-sofia.bg"},
    {"id": 3, "name": "Georgi Georgiev", "email": "georgi.georgiev@tu-sofia.bg"},
    {"id": 4, "name": "Elena Dimitrova", "email": "elena.dimitrova@tu-sofia.bg"},
]
COURSES = [
    {"id": 1, "code": "SA101", "title": "Software Architecture", "teacher": "Prof. Stoyanova", "capacity": 3},
    {"id": 2, "code": "AI201", "title": "Artificial Intelligence", "teacher": "Prof. Kolev", "capacity": 2},
    {"id": 3, "code": "DB150", "title": "Databases", "teacher": "Dr. Marinov", "capacity": 30},
    {"id": 4, "code": "PR102", "title": "Programming 2", "teacher": "Dr. Petkova", "capacity": 30},
]
ENROLLMENTS = [
    {"student_id": 1, "course_id": 1},
    {"student_id": 2, "course_id": 1},
    {"student_id": 1, "course_id": 3},
    {"student_id": 3, "course_id": 3},
    {"student_id": 2, "course_id": 2},
    {"student_id": 4, "course_id": 4},
]
