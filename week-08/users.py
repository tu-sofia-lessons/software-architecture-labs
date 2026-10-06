"""User directory of the identity provider (provided).

In a real university this lives in the identity provider (e.g. the central login
service), not in the platform. Roles: student, teacher, ta, admin.
"""
USERS = {
    "maria":          {"role": "student", "student_id": 1},
    "ivan":           {"role": "student", "student_id": 2},
    "prof.stoyanova": {"role": "teacher"},
    "prof.kolev":     {"role": "teacher"},
    "ta.georgieva":   {"role": "ta"},
    "registrar":      {"role": "admin"},
}
