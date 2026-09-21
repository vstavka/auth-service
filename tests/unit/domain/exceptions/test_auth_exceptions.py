import pytest

from src.domain.exceptions.auth import AccessTokenInvalidError
from src.shared.errors.codes import ErrorCode


@pytest.mark.unit
class TestAccessTokenInvalidError:
    def test_default_details_is_none(self) -> None:
        error = AccessTokenInvalidError()

        assert error.details is None
        assert error.code is ErrorCode.AUTH_ACCESS_TOKEN_INVALID
        assert error.message == "Access token is invalid or expired"

    def test_passes_details(self) -> None:
        error = AccessTokenInvalidError(details={"reason": "expired"})

        assert error.details == {"reason": "expired"}
