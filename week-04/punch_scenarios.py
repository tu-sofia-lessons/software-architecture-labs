"""Second Punch, Week 4 — released in class at 15:50.

A third source arrives: faculty lists (data/faculty.csv). Names are in CAPITALS, some names have stray
spaces, some e-mails have capital letters, and a `status` column marks students who withdrew; withdrawn
rows must not be imported. A student who withdrew and re-enrolled appears twice: first withdrawn, then active.
Unzip into your week-04 folder (it adds data/faculty.csv and this file), then run:  python verify.py --punch
"""


def scenarios(v):
    """v = the globals of verify.py (helpers such as StudentStore, import_cli)."""
    HERE = v["HERE"]

    def p1_faculty_pipeline_by_composition():
        if not (HERE / "data" / "faculty.csv").exists():
            raise AssertionError("data/faculty.csv is missing: unzip punch-04.zip into your week-04 folder")
        store = v["StudentStore"]()
        v["import_cli"].run_import("faculty", store)
        got = sorted((s["name"], s["email"]) for s in store.list_all())
        stored = {e for _, e in got}
        assert "georgi.georgiev@tu-sofia.bg" not in stored, "a withdrawn student was imported"
        assert "ivan.petrov@tu-sofia.bg" in stored, \
            "Ivan Petrov withdrew and re-enrolled (his active row comes later in the file) but was not imported: " \
            "which filter saw his withdrawn row first, and what did it keep?"
        assert got == [("Elena Dimitrova", "elena.dimitrova@tu-sofia.bg"),
                       ("Ivan Petrov", "ivan.petrov@tu-sofia.bg"),
                       ("Maria Ivanova", "maria.ivanova@tu-sofia.bg")], f"unexpected faculty import: {got}"

    return [("P1", "punch", "Second Punch: faculty pipeline built by composition", p1_faculty_pipeline_by_composition)]
