from fastapi import Request


def request_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


def request_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")
