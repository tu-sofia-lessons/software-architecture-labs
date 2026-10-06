"""Second Punch, Week 6 — released in class at 15:50.

The Dean needs the course fill report again (code, title, enrolled/capacity) — it used to be
one SQL JOIN. In remote mode the monolith no longer has the courses table.
Then: stop the Catalogue Service. Which user operations still work?
Unzip into your week-06 folder, then run:  python verify.py --punch
"""


def scenarios(v):
    """v = the globals of verify.py (CatalogueService, remote, app, reports ...)."""

    def p1_fill_report_by_api_composition():
        with v["CatalogueService"]():
            p = v["remote"]()
            v["app"].enroll_command(p, 1, 1)
            lines = v["reports"].fill_report(p)
            assert any("SA101" in l and "Software Architecture" in l and "1/3" in l for l in lines), \
                f"fill report in remote mode should show 'SA101 Software Architecture 1/3', got {lines}"
            assert len(lines) == 4, "one line per course"

    def p2_service_down_partial_availability():
        with v["CatalogueService"]() as svc:
            p = v["remote"]()
            svc.stop()
            assert len(p.students.list_students()) == 4, "students must still work without the catalogue"
            ok, msg = v["app"].enroll_command(p, 1, 1)
            assert not ok and "unavailable" in msg.lower(), f"enroll should fail with a clear message, got {msg!r}"

    return [
        ("P1", "punch", "Second Punch: fill report works in remote mode (API composition)", p1_fill_report_by_api_composition),
        ("P2", "punch", "Second Punch: service down -> students work, enroll fails clearly", p2_service_down_partial_availability),
    ]
