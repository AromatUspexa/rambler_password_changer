class RamblerException(Exception):
    pass

class LoginFailed(RamblerException):
    pass

class BanAccount(RamblerException):
    pass
