"""The model boundary: the ONLY place that knows which LLM is used (provided).

LLM_BACKEND=fake    (default) deterministic offline stand-in, no network
LLM_BACKEND=ollama  local Ollama, model from OLLAMA_MODEL (default llama3.2)
LLM_BACKEND=openai  any OpenAI-compatible API: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
"""
import json
import os
import re
import urllib.request

CALLS = {"count": 0}          # how many times the model was called (the fake is cheap; a real one is not)


def generate(prompt: str) -> str:
    """Send a prompt to the configured model and return its text answer."""
    CALLS["count"] += 1
    backend = os.environ.get("LLM_BACKEND", "fake")
    if backend == "ollama":
        return _ollama(prompt)
    if backend == "openai":
        return _openai(prompt)
    return fake_llm(prompt)


# ------------------------------------------------------------------ real backends
def _post_json(url, payload, headers=None):
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})}, method="POST")
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def _ollama(prompt):
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    reply = _post_json("http://localhost:11434/api/generate",
                       {"model": model, "prompt": prompt, "stream": False})
    return reply["response"].strip()


def _openai(prompt):
    base = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    reply = _post_json(
        f"{base}/chat/completions",
        {"model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
         "messages": [{"role": "user", "content": prompt}], "temperature": 0},
        headers={"Authorization": f"Bearer {os.environ.get('LLM_API_KEY', '')}"})
    return reply["choices"][0]["message"]["content"].strip()


# ------------------------------------------------------------------ fake model
_INVENTED = [   # what a model "knows" without our documents: fluent, confident, wrong
    ("pass", "To pass the course you need at least 50% attendance and 60% of the points on the final exam."),
    ("rector", "The rector is elected by the General Assembly for a five-year term and currently holds office until 2029."),
    ("parking", "Student parking costs €2 per day and a semester card costs €60."),
    ("erasmus", "For Erasmus you only need a motivation letter; the deadline is usually in May."),
    ("exam", "Exams can be retaken as many times as needed during the academic year."),
]
_WORD = re.compile(r"\w+")


def _words(text):
    return {w for w in _WORD.findall(text.lower()) if len(w) > 2}


def fake_llm(prompt: str) -> str:
    """Deterministic stand-in. Without CONTEXT it invents; with CONTEXT it copies the best sentences."""
    question = prompt.split("QUESTION:", 1)[1] if "QUESTION:" in prompt else prompt
    question = question.split("ANSWER:", 1)[0].strip()
    if "CONTEXT:" not in prompt:
        for keyword, answer in _INVENTED:
            if keyword in question.lower():
                return answer
        return "Usually this is handled by the Student Office, and the deadline is two weeks before the exam."

    context = prompt.split("CONTEXT:", 1)[1].split("QUESTION:", 1)[0]
    marker, scored = "", []
    for line in context.splitlines():
        line = line.strip()
        if line.startswith("["):
            marker = line[: line.index("]") + 1] if "]" in line else line
            line = line[len(marker):].strip()
        for sentence in re.split(r"(?<!Prof\.)(?<!Dr\.)(?<=[.!?])\s+", line):
            overlap = len(_words(sentence) & _words(question))
            if sentence and overlap:
                scored.append((overlap, len(scored), sentence, marker))
    if not scored:
        return "The provided documents do not contain this information."
    best = sorted(scored, key=lambda s: (-s[0], s[1]))[:2]
    return " ".join(f"{sentence} {marker}".strip() for _, _, sentence, marker in best)
