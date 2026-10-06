"""Staff command-line tool (Second Punch, provided). A second entry point: it calls the application
layer directly, without going through api.py.

    python admin_cli.py grade <login> <student_id> <course_id> <grade>
    python admin_cli.py gradebook <login> <course_id>

The login is taken from the staff member's workstation session (here: from the argument).
If your service functions take the caller differently, adapt the two calls below.
"""
import sys

import errors
import service
import users
from identity import Principal


def principal_for(login):
    """Who is at the keyboard (in real life: the workstation's single sign-on)."""
    user = users.USERS[login]
    return Principal(login, user["role"], user.get("student_id"))


def grade(principal, student_id, course_id, value):
    service.submit_grade(principal, student_id, course_id, value)


def gradebook(principal, course_id):
    return service.course_gradebook(principal, course_id)


def main(argv):
    command, login, *rest = argv
    principal = principal_for(login)
    try:
        if command == "grade":
            grade(principal, int(rest[0]), int(rest[1]), float(rest[2]))
            print("grade recorded")
        elif command == "gradebook":
            print(gradebook(principal, int(rest[0])))
    except errors.Forbidden as e:
        print("FORBIDDEN:", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
