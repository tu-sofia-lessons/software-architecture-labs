"""In-process façade over the University Platform (provided).

It enforces the BUSINESS rules (W1: unknown student/course, duplicate, capacity).
It trusts its caller: like an internal service called with a service account,
it does NOT know which human is behind a request. That is the agent side's job.
"""
import re
from pathlib import Path

STUDENTS = {1: "Maria Ivanova", 2: "Ivan Petrov", 3: "Georgi Georgiev", 4: "Elena Dimitrova"}
COURSES = {
    1: {"id": 1, "code": "SA101", "title": "Software Architecture", "capacity": 3},
    2: {"id": 2, "code": "AI201", "title": "Artificial Intelligence", "capacity": 2},
    3: {"id": 3, "code": "DB150", "title": "Databases", "capacity": 30},
    4: {"id": 4, "code": "PR102", "title": "Programming 2", "capacity": 30},
}
ENROLLMENTS = {(1, 1), (2, 1), (2, 2)}      # Maria: SA101 · Ivan: SA101, AI201

_STOP = {"a", "the", "and", "of", "to", "in", "for", "is", "are", "what", "which", "my", "me", "i", "do"}


class EnrollmentError(Exception):
    """A request that breaks a business rule."""


class Platform:
    def __init__(self, knowledge_dir):
        self.enrollments = set(ENROLLMENTS)
        self.knowledge_dir = Path(knowledge_dir)

    # ---------------------------------------------------------------- reads
    def find_student(self, name):
        for sid, full in STUDENTS.items():
            if name.lower() in full.lower().split():
                return {"id": sid, "name": full}
        return None

    def find_course(self, query):
        q = query.lower().strip()
        for course in COURSES.values():
            if q in (course["code"].lower(), course["title"].lower()) or q in course["title"].lower():
                return dict(course)
        return None

    def courses_of(self, student_id):
        return [dict(COURSES[c]) for s, c in sorted(self.enrollments) if s == student_id]

    def seats(self, course_id):
        course = COURSES.get(course_id)
        if course is None:
            raise EnrollmentError(f"Unknown course {course_id}")
        taken = sum(1 for _, c in self.enrollments if c == course_id)
        return {"code": course["code"], "capacity": course["capacity"], "taken": taken,
                "free": course["capacity"] - taken}

    def search_docs(self, query, top_k=2):
        """W9-style retrieval: paragraphs ranked by word overlap."""
        words = {w for w in re.findall(r"\w+", query.lower()) if w not in _STOP}
        ranked = []
        for path in sorted(self.knowledge_dir.glob("*.txt")):
            body = path.read_text(encoding="utf-8").partition("\n\n")[2]
            for paragraph in body.split("\n\n"):
                paragraph = " ".join(paragraph.split())
                score = len(words & set(re.findall(r"\w+", paragraph.lower())))
                if score >= 1:
                    ranked.append((-score, path.name, paragraph))
        return [{"source": src, "text": text} for _, src, text in sorted(ranked)[:top_k]]

    # ---------------------------------------------------------------- writes
    def enroll(self, student_id, course_id):
        if student_id not in STUDENTS:
            raise EnrollmentError(f"Unknown student {student_id}")
        seats = self.seats(course_id)
        if (student_id, course_id) in self.enrollments:
            raise EnrollmentError("Student is already enrolled in this course")
        if seats["free"] <= 0:
            raise EnrollmentError(f"{seats['code']} is full")
        self.enrollments.add((student_id, course_id))
        return {"enrolled": STUDENTS[student_id], "course": seats["code"]}

    def drop(self, student_id, course_id):
        if (student_id, course_id) not in self.enrollments:
            raise EnrollmentError("Student is not enrolled in this course")
        self.enrollments.remove((student_id, course_id))
        return {"dropped": STUDENTS[student_id], "course": COURSES[course_id]["code"]}
