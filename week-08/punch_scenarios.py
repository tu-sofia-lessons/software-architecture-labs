"""Second Punch, Week 8 — released in class at 15:50.

New role: teaching assistant. ta.georgieva (already in users.py, assistant of SA101 in store.py)
may VIEW the SA101 gradebook, but may not grade and may not read student transcripts.
It also brings admin_cli.py, the staff tool: a second entry point that calls the application layer
directly, without api.py. The same rules must hold there too (P2).
Unzip into your week-08 folder, then run:  python verify.py --punch
"""


def scenarios(v):
    """v = the globals of verify.py (helpers: api_server, call, as_)."""

    def p1_teaching_assistant():
        with v["api_server"]():
            own, _ = v["call"]("GET", "/courses/1/grades", v["as_"]("ta.georgieva"))
            other, _ = v["call"]("GET", "/courses/2/grades", v["as_"]("ta.georgieva"))
            grade, _ = v["call"]("POST", "/grades", v["as_"]("ta.georgieva"),
                                 {"student_id": 1, "course_id": 1, "grade": 6.0})
            transcript, _ = v["call"]("GET", "/students/1/grades", v["as_"]("ta.georgieva"))
        got = {"view SA101": own, "view AI201": other, "submit SA101": grade, "transcript": transcript}
        expected = {"view SA101": 200, "view AI201": 403, "submit SA101": 403, "transcript": 403}
        assert got == expected, f"expected {expected}, got {got}"

    def p2_second_entry_point():
        import admin_cli
        import errors
        import store
        ta = admin_cli.principal_for("ta.georgieva")
        before = dict(store.GRADES)
        try:
            admin_cli.grade(ta, 1, 1, 6.0)
        except errors.Forbidden:
            pass
        else:
            raise AssertionError("admin_cli.py let the teaching assistant grade SA101: do your rules still "
                                 "hold when the service is called without api.py?")
        assert store.GRADES == before, "a denied grade must not change any data"
        admin_cli.gradebook(ta, 1)                       # the TA may view the SA101 gradebook here too

    return [("P1", "punch", "Second Punch: teaching assistant views SA101 grades only, cannot grade",
             p1_teaching_assistant),
            ("P2", "punch", "Second Punch: the same rules hold for a second entry point (admin_cli.py)",
             p2_second_entry_point)]
