"""All reports of the platform. Every new report means editing this file."""
import csv
import io

AVAILABLE = ["csv", "txt"]


class UnknownReport(Exception):
    """No report with that name."""


def generate(name, data):
    """Produce the report called `name` from the ReportData snapshot."""
    if name == "csv":
        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["id", "name", "email"])
        for s in data.students:
            writer.writerow([s["id"], s["name"], s["email"]])
        return out.getvalue()
    elif name == "txt":
        lines = ["UNIVERSITY STUDENTS REPORT", ""]
        for s in data.students:
            lines.append(f"{s['id']}. {s['name']} <{s['email']}>")
        return "\n".join(lines) + "\n"
    # Dean's Office asked for course fill statistics ... Erasmus Office wants JSON ... Quality Office ...
    raise UnknownReport(name)
