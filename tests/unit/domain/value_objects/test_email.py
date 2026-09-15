from dataclasses import FrozenInstanceError

import pytest

from src.domain.exceptions.email import InvalidEmailError
from src.domain.value_objects import Email
from src.shared.errors.codes import ErrorCode


class TestEmail:

    def test_stores_normalized_value(self):
        email = Email("User@YANDEX.COM")
        assert email.value == "User@yandex.com"

    def test_converts_to_string(self):
        email = Email("User@YANDEX.COM")
        assert str(email) == "User@yandex.com"

    def test_with_same_value_is_equal(self):
        first = Email("User@YANDEX.COM")
        second = Email("User@yandex.com")
        assert first == second

    def test_with_different_value_is_not_equal(self):
        first = Email("User@YANDEX.COM")
        second = Email("User2@yandex.com")
        assert first != second

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "",
            "not-an-email",
            "user@",
            "@example.com",
            "user @example.com",
            "user@localhost",
        ],
    )
    def test_raises_invalid_email_error_for_invalid_value(self, invalid_value):
        with pytest.raises(InvalidEmailError) as error:
            Email(invalid_value)
        assert error.value.code is ErrorCode.AUTH_INVALID_EMAIL

    def test_is_immutable(self):
        email = Email("User@YANDEX.COM")
        with pytest.raises(FrozenInstanceError):
            email.value = "User2@yandex.com"
