"""The tools the agent may use (provided). A tool = name + kind + argument schema + function."""
from dataclasses import dataclass
from typing import Callable

from platform_api import EnrollmentError, Platform

READ, WRITE = "read", "write"


@dataclass(frozen=True)
class Tool:
    name: str
    kind: str                      # READ changes nothing; WRITE changes the platform
    params: dict                   # argument name -> Python type
    description: str
    fn: Callable


def build_tools(platform: Platform) -> dict:
    tools = [
        Tool("find_student", READ, {"name": str}, "Find a student by (part of) their name.", platform.find_student),
        Tool("find_course", READ, {"query": str}, "Find a course by code or title.", platform.find_course),
        Tool("list_my_courses", READ, {"student_id": int}, "Courses a student is enrolled in.", platform.courses_of),
        Tool("course_seats", READ, {"course_id": int}, "Capacity, taken and free seats of a course.", platform.seats),
        Tool("search_docs", READ, {"query": str}, "Search the university documents.", platform.search_docs),
        Tool("enroll", WRITE, {"student_id": int, "course_id": int}, "Enroll a student in a course.", platform.enroll),
        Tool("drop_course", WRITE, {"student_id": int, "course_id": int}, "Remove a student from a course.", platform.drop),
    ]
    return {t.name: t for t in tools}


def execute(tools: dict, call: dict):
    """Run one tool call and return its result (errors become {'error': ...})."""
    tool = tools.get(call.get("action"))
    if tool is None:
        return {"error": f"unknown tool {call.get('action')!r}"}
    try:
        return tool.fn(**call.get("args", {}))
    except (EnrollmentError, TypeError, KeyError) as e:
        return {"error": str(e)}
