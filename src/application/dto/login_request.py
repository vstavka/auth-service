from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoginRequest:
    email: str
    password: str
    ip: str | None = None
    user_agent: str | None = None
    device_info: str | None = None
