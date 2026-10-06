"""Stand-in for the university mail server (provided). It is flaky: set .down = True or MAIL_DOWN=1."""
import os


class MailServerDown(Exception):
    """The mail server did not accept the message."""


class Mailer:
    def __init__(self):
        self.down = os.environ.get("MAIL_DOWN") == "1"
        self.outbox = []            # messages that were really sent

    def send(self, to, subject, body):
        if self.down:
            raise MailServerDown(f"cannot deliver to {to}")
        self.outbox.append({"to": to, "subject": subject, "body": body})
