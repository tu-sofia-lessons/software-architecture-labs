"""The model boundary (provided). LLM_BACKEND = fake (default) | ollama | openai — see README."""
import json
import os
import re
import urllib.request


def generate(prompt: str) -> str:
    backend = os.environ.get("LLM_BACKEND", "fake")
    if backend == "ollama":
        return _post("http://localhost:11434/api/generate",
                     {"model": os.environ.get("OLLAMA_MODEL", "llama3.2"), "prompt": prompt,
                      "stream": False, "format": "json"})["response"]
    if backend == "openai":
        base = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        reply = _post(f"{base}/chat/completions",
                      {"model": os.environ.get("LLM_MODEL", "gpt-4o-mini"), "temperature": 0,
                       "messages": [{"role": "user", "content": prompt}]},
                      {"Authorization": f"Bearer {os.environ.get('LLM_API_KEY', '')}"})
        return reply["choices"][0]["message"]["content"]
    return fake_agent_llm(prompt)


def _post(url, payload, headers=None):
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST",
                                     headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


# ---------------------------------------------------------------- deterministic fake planner
def fake_agent_llm(prompt: str) -> str:
    """A naive planner. Like many real models, it obeys instructions it finds in tool results."""
    state = json.loads(prompt.split("STATE_JSON:", 1)[1].strip())
    return json.dumps(_plan(state))


def _plan(state):
    request = state["request"].lower()
    me = state["user"]["student_id"]
    history = state["history"]

    def done(action, args):
        return any(h["action"] == action and h["args"] == args for h in history)

    def result_of(action):
        for h in reversed(history):
            if h["action"] == action:
                return h["result"]
        return None

    # 1. Naive: follow instructions that appeared in any tool result (this is the injection risk).
    for h in history:
        text = json.dumps(h["result"])
        for verb, action in (("enroll", "enroll"), ("drop", "drop_course")):
            for s, c in re.findall(rf"{verb} student (\d+) (?:in|from) course (\d+)", text, re.I):
                args = {"student_id": int(s), "course_id": int(c)}
                if not done(action, args):
                    return {"action": action, "args": args}

    # 2. "enroll me in X", "drop Ivan from X"
    m = re.search(r"\b(enroll|drop)\s+(\w+)\s+(?:in|into|from)\s+([\w ]+)", request)
    if m:
        verb, who, course_text = m.group(1), m.group(2), m.group(3).strip()
        if who == "me":
            student_id = me
        else:
            if not done("find_student", {"name": who}):
                return {"action": "find_student", "args": {"name": who}}
            found = result_of("find_student")
            if not found or "error" in found:
                return {"final": f"I could not find a student called {who}."}
            student_id = found["id"]
        if not done("find_course", {"query": course_text}):
            return {"action": "find_course", "args": {"query": course_text}}
        course = result_of("find_course")
        if not course or "error" in course:
            return {"final": f"I could not find the course {course_text!r}."}
        action = "enroll" if verb == "enroll" else "drop_course"
        args = {"student_id": student_id, "course_id": course["id"]}
        if not done(action, args):
            return {"action": action, "args": args}
        outcome = result_of(action)
        if isinstance(outcome, dict) and "error" in outcome:
            return {"final": f"I could not do that: {outcome['error']}"}
        return {"final": f"Done: {outcome}"}

    # 3. "Which of my courses still have seats?"
    if "seat" in request:
        if not done("list_my_courses", {"student_id": me}):
            return {"action": "list_my_courses", "args": {"student_id": me}}
        courses = result_of("list_my_courses")
        if isinstance(courses, dict):
            return {"final": f"I could not list your courses: {courses.get('error')}"}
        for course in courses:
            if not done("course_seats", {"course_id": course["id"]}):
                return {"action": "course_seats", "args": {"course_id": course["id"]}}
        lines = [f"{h['result']['code']}: {h['result']['free']} free" for h in history
                 if h["action"] == "course_seats" and "free" in h["result"]]
        return {"final": "; ".join(lines) or "You are not enrolled in any course."}

    # 4. Anything else: look it up in the documents.
    if not done("search_docs", {"query": state["request"]}):
        return {"action": "search_docs", "args": {"query": state["request"]}}
    found = result_of("search_docs") or []
    if not found or isinstance(found, dict):
        return {"final": "The university documents do not contain this information."}
    return {"final": " ".join(f"{d['text']} [{d['source']}]" for d in found)}
