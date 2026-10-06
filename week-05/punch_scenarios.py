"""Second Punch, Week 5 — released in class at 15:50.

Part 1: the Library must open an account for every newly enrolled student. Add library.py
(a Library with `accounts` and `on_student_enrolled`), create it and subscribe it in app.build()
and expose it as `library`. Part 2: run the async bus while the mail server is down.
Unzip into your week-05 folder, then run:  python verify.py --punch
"""


def scenarios(v):
    """v = the globals of verify.py (helpers such as app)."""
    app = v["app"]

    def p1_library_reacts_without_producer_change():
        a = app.build()
        assert hasattr(a, "library"), "app.build() should create and wire a library component"
        a.service.enroll(4, 3)
        a.bus.drain()
        assert 4 in a.library.accounts, "the Library did not create an account for student 4"
        b = app.build()
        b.bus.handlers.clear()          # nobody is listening any more
        b.service.enroll(3, 3)
        b.bus.drain()
        assert 3 not in b.library.accounts, ("with no subscribers the Library still opened an account: "
                                             "the producer reaches the Library directly, not through the event")

    def p2_async_failed_notification_is_lost():
        a = app.build(mode="async")
        a.mailer.down = True
        a.service.enroll(1, 3)          # returns immediately; handlers run later
        a.bus.drain()
        a.mailer.down = False           # the mail server recovers ...
        a.bus.drain()
        assert (1, 3) in a.service.enrollments and a.bus.errors, "enrollment should succeed, the failure recorded"
        assert a.mailer.outbox == [], "unexpected: the in-memory bus has no retry"
        # Observation, not a bug to fix today: the notification is gone. What would you need? (Week 7)

    return [("P1", "punch", "Second Punch: the Library reacts to enrollments (0 lines in enrollment.py)", p1_library_reacts_without_producer_change),
            ("P2", "punch", "Second Punch: async + mail down -> the notification is lost (observe why)", p2_async_failed_notification_is_lost)]
