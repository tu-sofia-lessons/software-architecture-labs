"""Dean's course fill report."""


def fill_report(platform):
    """One line per course: code, title, enrolled/capacity."""
    rows = platform.conn.execute(
        "SELECT c.code, c.title, c.capacity, COUNT(e.student_id) AS enrolled "
        "FROM courses c LEFT JOIN enrollments e ON e.course_id = c.id "
        "GROUP BY c.id ORDER BY c.id"
    )
    return [f"{r['code']}  {r['title']:<25} {r['enrolled']}/{r['capacity']}" for r in rows]
