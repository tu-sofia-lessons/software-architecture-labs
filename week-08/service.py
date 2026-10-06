"""Grades and enrollment operations (the application layer)."""
import store


class NotFound(Exception):
    """The student or course does not exist."""


class Conflict(Exception):
    """The request contradicts the current state (e.g. already enrolled)."""


def _require_student(student_id):
    if student_id not in store.STUDENTS:
        raise NotFound(f"unknown student {student_id}")


def _require_course(course_id):
    if course_id not in store.COURSES:
        raise NotFound(f"unknown course {course_id}")


def grades_of_student(student_id):
    """All grades of one student (their transcript)."""
    _require_student(student_id)
    return [{"course": store.COURSES[c]["code"], "grade": g}
            for (s, c), g in sorted(store.GRADES.items()) if s == student_id]


def course_gradebook(course_id):
    """All grades in one course (the teacher's gradebook)."""
    _require_course(course_id)
    return [{"student_id": s, "grade": g}
            for (s, c), g in sorted(store.GRADES.items()) if c == course_id]


def submit_grade(student_id, course_id, grade):
    _require_student(student_id)
    _require_course(course_id)
    if (student_id, course_id) not in store.ENROLLMENTS:
        raise ValueError("student is not enrolled in this course")
    if not 2.0 <= float(grade) <= 6.0:
        raise ValueError("grade must be between 2.00 and 6.00")
    store.GRADES[(student_id, course_id)] = float(grade)


def enroll(student_id, course_id):
    _require_student(student_id)
    _require_course(course_id)
    if (student_id, course_id) in store.ENROLLMENTS:
        raise Conflict("already enrolled")
    taken = sum(1 for _, c in store.ENROLLMENTS if c == course_id)
    if taken >= store.COURSES[course_id]["capacity"]:
        raise Conflict("course is full")
    store.ENROLLMENTS.add((student_id, course_id))
