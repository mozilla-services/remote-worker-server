"""Remote workers exceptions."""


class NotAuthenticatedError(Exception):
    pass


class BackendError(Exception):
    """A generic exception raised by storage on error.

    :param original: the wrapped exception raised by underlying library.
    :type original: Exception
    """
    def __init__(self, original=None, *args, **kwargs):
        self.original = original
        super(BackendError, self).__init__(*args, **kwargs)
