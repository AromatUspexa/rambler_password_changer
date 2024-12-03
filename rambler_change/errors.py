class RamblerException(Exception):
    pass


class LoginFailed(RamblerException):
    pass


class BanAccount(RamblerException):
    pass


class PasswordChangeFailed(RamblerException):
    pass


class CaptchaError(RamblerException):
    pass


class CaptchaTaskCreationError(CaptchaError):
    pass


class CaptchaSolutionError(CaptchaError):
    pass


class BadDataAccount(RamblerException):
    pass


class PlaywrightError(RamblerException):
    pass


class ResponseCodeFailure(PlaywrightError):
    pass


class PageCloseError(PlaywrightError):
    pass


class AttemptsErrorReached(RamblerException):
    pass





