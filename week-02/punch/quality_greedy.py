"""Quality Office: "summary" report that tries to add a totals row to the platform's data."""

NAME = "quality-summary"


def generate(data):
    data.students.append({"id": 0, "name": "TOTAL", "email": "-"})   # modifies the core's data?
    return f"{len(data.students)} rows\n"
