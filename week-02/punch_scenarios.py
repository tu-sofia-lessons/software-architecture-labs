"""Second Punch, Week 2 -- released in class at 15:50.

The Quality Office ships two plug-ins it wrote itself (in punch/): one fails already at import,
the other tries to add a "TOTAL" row to the platform's data. Then the core team adds an optional
FORMAT field to the contract ("csv" | "text" | "json"; default "text") and `python cli.py reports`
must show each report's format next to its name.
Unzip into your week-02 folder, then run:  python verify.py --punch
"""

WITH_FORMAT = '''NAME = "probe-new"
FORMAT = "json"
def generate(data):
    return "{}\\n"
'''


def scenarios(v):
    """v = the globals of verify.py (helpers such as cli, dropped_plugin, report_names, HERE, PROBE)."""
    dropped_plugin, report_names, cli, HERE = v["dropped_plugin"], v["report_names"], v["cli"], v["HERE"]

    def p1_broken_faculty_plugins():
        with dropped_plugin("quality_broken.py", copy_from=HERE / "punch" / "quality_broken.py"), \
                dropped_plugin("quality_greedy.py", copy_from=HERE / "punch" / "quality_greedy.py"):
            names = report_names()
            assert "quality-summary" in names, "the greedy plug-in fulfils the contract and must be listed"
            assert "csv" in names and "quality-survey" not in names, "import-time failure must skip only that plug-in"
            code, out, err = cli("report", "quality-summary")
            assert "Traceback" not in err, "the greedy plug-in must not crash the CLI"

    def p2_optional_format_keeps_old_plugins():
        with dropped_plugin("probe_json.py", WITH_FORMAT), dropped_plugin("probe_report.py", v["PROBE"]):
            # name -> the rest of its line (the name itself is cut off, so it cannot satisfy the check)
            lines = {l.split()[0]: l.strip()[len(l.split()[0]):] for l in report_names().splitlines() if l.strip()}
            assert "probe-new" in lines and "probe" in lines, "old plug-ins (no FORMAT) and new ones must both load"
            assert "json" in lines["probe-new"], "`reports` must show the declared FORMAT next to the name"
            assert "text" in lines["probe"], "a plug-in without FORMAT must be shown with the default format 'text'"

    return [
        ("P1", "punch", "Second Punch: faculty plug-ins broken at import / greedy are contained", p1_broken_faculty_plugins),
        ("P2", "punch", "Second Punch: optional FORMAT (default 'text') keeps old plug-ins working", p2_optional_format_keeps_old_plugins),
    ]
