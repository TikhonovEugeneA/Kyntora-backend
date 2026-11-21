from fastapi import HTTPException, status

_BEARER = {"WWW-Authenticate": "Bearer"}


class InvalidToken(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid Token.",
            _BEARER,
        )


class ExpiredRefreshToken(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            "The refresh token has expired.",
            _BEARER,
        )


class InvalidCredentials(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid login or password.",
            _BEARER,
        )


class UserAlreadyExists(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "User with current login already exists.",
        )
