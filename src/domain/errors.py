class BotError(Exception):
    """Base error safe for application-level translation."""


class MalformedInputError(BotError):
    pass


class ProviderError(BotError):
    pass


class ProviderQuotaError(ProviderError):
    pass


class ProviderUnavailableError(ProviderError):
    pass


class AnalysisTimeoutError(ProviderError):
    pass


class ProcessingError(BotError):
    pass


class FileTooLargeError(ProcessingError):
    pass
