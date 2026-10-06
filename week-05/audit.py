"""Compliance audit log (provided). Law: every enrollment must have an audit record."""


class AuditUnavailable(Exception):
    """The audit store could not write the record."""


class AuditLog:
    def __init__(self):
        self.down = False
        self.records = []

    def record(self, action, **details):
        if self.down:
            raise AuditUnavailable(action)
        self.records.append({"action": action, **details})
