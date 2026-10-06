"""Second Punch, Week 7 — released in class at 15:50.

Registration week: the Catalogue answers every request in 1.5 s and 20 users check a course
at the same moment. Load NFR for degradation (from the Registrar and Faculty IT):
    at least 80% of the capacity checks still succeed (the service is slow, not broken),
    our client may cause AT MOST 2x the normal call rate (normal = 1 call per operation),
    and the user must get an answer (success or clear failure) in < 4 s (p95).
Compare your client with the naive one:  python loadgen.py --users 20 [--naive]
(start the service yourself first: python catalog_service/run.py --delay 1.5)
Unzip into your week-07 folder, then run:  python verify.py --punch
The file also brings S8, a reference-path hint (shown, never graded).
"""


def scenarios(v):
    """v = the globals of verify.py (CatalogueService, URL, platform, timed, service_calls ...)."""

    def p1_load_nfr_during_degradation():
        import loadgen
        with v["CatalogueService"]("--delay", "1.5"):
            naive = loadgen.run(users=20, naive=True, url=v["URL"])
            mine = loadgen.run(users=20, naive=False, url=v["URL"])
        assert naive["calls_per_op"] >= 4, f"(sanity) the naive client should amplify load, got {naive}"
        assert mine["ok"] >= 0.8 * mine["ops"], (f"only {mine['ok']}/{mine['ops']} checks succeeded against a service "
                                                 f"that is slow (1.5 s), not broken (NFR: >= 80%). Is your timeout "
                                                 f"shorter than the service's latency? {mine}")
        assert mine["calls_per_op"] <= 2.0, (f"your client causes {mine['calls_per_op']} calls per operation on a slow "
                                             f"service (NFR: at most 2x; naive: {naive['calls_per_op']})")
        assert mine["p95_s"] < 4.0, f"p95 latency {mine['p95_s']} s (NFR: < 4 s)"

    def s8_reference_policy_does_not_retry_timeouts():
        with v["CatalogueService"]("--delay", "5"):
            p = v["platform"]()
            before = v["service_calls"]()
            v["timed"](p.catalog.get_course, 1)
            v["time"].sleep(0.2)
            calls = v["service_calls"]() - before
        assert calls == 1, (f"the reference policy does not retry a timeout (a slow service is usually an overloaded "
                            f"one); yours made {calls} calls. Fine if your ADR argues it and P1 still holds")

    return [("P1", "punch", "Second Punch: load NFR on a slow service (>= 80% ok, <= 2x calls, p95 < 4 s)",
             p1_load_nfr_during_degradation),
            ("S8", "path", "Reference policy: a timeout is not retried", s8_reference_policy_does_not_retry_timeouts)]
