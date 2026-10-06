"""Errors of the application layer (provided). api.run_service turns Forbidden into 403 Forbidden."""


class Forbidden(Exception):
    """The caller is authenticated but not allowed to do this."""
