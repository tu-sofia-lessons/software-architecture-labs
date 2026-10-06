"""Second Punch, Week 3 -- released in class at 15:50.

Faculty IT deployed version 2 of the file server API (file_server.py in this zip):
    GET /courses/<id>/materials -> {"files": [{"name": "...", "size": 123}, ...]}
Unzip into your week-03 folder (it replaces file_server.py), then run:  python verify.py --punch
"""


def scenarios(v):
    """v = the globals of verify.py (helpers such as file_server and cli)."""

    def p1_file_server_api_v2():
        with v["file_server"]("--v2"):
            code, out, err, *_ = v["cli"]("materials", "list", "1", backend="remote")
        # each listed file starts its own line (extra columns such as a size are fine: option C)
        assert code == 0 and any(line.split()[:1] == ["lecture01.txt"] for line in out.splitlines()), \
            f"list must work against API v2, got:\n{out}{err[-300:]}"

    return [("P1", "punch", "Second Punch: file server API v2 still works", p1_file_server_api_v2)]
