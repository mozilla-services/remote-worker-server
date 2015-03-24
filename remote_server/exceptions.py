"""Remote workers exceptions."""


class Error(Exception):
    """Base error class for all Remote Server exceptions."""
    pass


class OutOfProtocolError(Error):
    """Base error class for undefined out-of-protocol error conditions.

    Such errors will typically be raised if a server is behaving badly, e.g.
    returning invalid JSON responses.  These are typically fatal as they
    mean that a piece of the infra is not acting as it should.
    """
    pass


class NotAuthenticatedError(Error):
    pass


class BackendError(Error):
    """A generic exception raised by storage on error.

    :param original: the wrapped exception raised by underlying library.
    :type original: Exception
    """
    def __init__(self, original=None, *args, **kwargs):
        self.original = original
        super(BackendError, self).__init__(*args, **kwargs)


class ScopeMismatchError(Error):
    """Error raised when the OAuth scopes do not match."""

    def __init__(self, provided, required):
        message = "scope {0} does not match {1}".format(provided, required)
        super(ScopeMismatchError, self).__init__(message)
