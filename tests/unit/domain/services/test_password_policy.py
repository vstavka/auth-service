import pytest

from src.domain.exceptions.password import InvalidPasswordError
from src.domain.services.password_policy import PasswordPolicy


@pytest.fixture
def password_policy() -> PasswordPolicy:
    return PasswordPolicy(
        min_length=12,
        max_length=128,
    )


@pytest.mark.unit
class TestPasswordPolicy:
    @pytest.mark.parametrize(
        "password",
        [
            "Password123!",
            "StrongPassword2026!",
            "ДлинныйПароль123!",
            "пароль123!длинный",
            "Correct-Horse-123!",
        ],
    )
    def test_accepts_valid_passwords(
            self,
            password_policy: PasswordPolicy,
            password: str,
    ):
        password_policy.validate(password)

    def test_accepts_password_of_exact_minimum_length(
            self,
            password_policy: PasswordPolicy,
    ):
        password = "Abcdefghij1!"

        password_policy.validate(password)

    def test_accepts_password_of_exact_maximum_length(
            self,
            password_policy: PasswordPolicy,
    ):
        password = "A1!" + ("a" * 125)

        password_policy.validate(password)

    @pytest.mark.parametrize(
        "password",
        [
            "",
            "Abcdefgh1!",
            "12345678901",
        ],
    )
    def test_rejects_password_shorter_than_minimum_length(
            self,
            password_policy: PasswordPolicy,
            password: str,
    ):
        with pytest.raises(InvalidPasswordError) as error:
            password_policy.validate(password)

        assert error.value.details["reason"] == "too_short"

    def test_rejects_password_longer_than_maximum_length(
            self,
            password_policy: PasswordPolicy,
    ):
        password = "A1!" + ("a" * 126)

        with pytest.raises(InvalidPasswordError) as error:
            password_policy.validate(password)

        assert error.value.details["reason"] == "too_long"

    def test_rejects_password_without_letters(
            self,
            password_policy: PasswordPolicy,
    ):
        password = "12345678901!"

        with pytest.raises(InvalidPasswordError) as error:
            password_policy.validate(password)

        assert error.value.details["reason"] == "no_letter"

    def test_rejects_password_without_digits(
            self,
            password_policy: PasswordPolicy,
    ):
        password = "PasswordOnly!"

        with pytest.raises(InvalidPasswordError) as error:
            password_policy.validate(password)

        assert error.value.details["reason"] == "no_digit"

    def test_rejects_password_without_special_characters(
            self,
            password_policy: PasswordPolicy,
    ):
        password = "Password1234"

        with pytest.raises(InvalidPasswordError) as error:
            password_policy.validate(password)

        assert error.value.details["reason"] == "no_special_character"

    def test_accepts_cyrillic_letter_as_letter(
            self,
            password_policy: PasswordPolicy,
    ):
        password = "Пароль123!Тест"

        password_policy.validate(password)

    def test_accepts_whitespace_when_other_rules_are_satisfied(
            self,
            password_policy: PasswordPolicy,
    ):
        password = "Long password 123!"

        password_policy.validate(password)

    def test_too_short_details_include_min_length(
            self,
            password_policy: PasswordPolicy,
    ):
        with pytest.raises(InvalidPasswordError) as error:
            password_policy.validate("short")

        assert error.value.details["min_length"] == 12
        assert error.value.details["reason"] == "too_short"

    def test_too_long_details_include_max_length(
            self,
            password_policy: PasswordPolicy,
    ):
        with pytest.raises(InvalidPasswordError) as error:
            password_policy.validate("A1!" + ("a" * 126))

        assert error.value.details["max_length"] == 128
        assert error.value.details["reason"] == "too_long"

    def test_validate_respects_custom_min_and_max_length(self):
        policy = PasswordPolicy(min_length=8, max_length=20)

        with pytest.raises(InvalidPasswordError) as too_short:
            policy.validate("Ab1!xxx")
        assert too_short.value.details["reason"] == "too_short"

        policy.validate("Abcdef1!")

        with pytest.raises(InvalidPasswordError) as too_long:
            policy.validate("A1!" + ("a" * 18))
        assert too_long.value.details["reason"] == "too_long"

    def test_rejects_password_with_whitespace_but_no_special_character(
            self,
            password_policy: PasswordPolicy,
    ):
        with pytest.raises(InvalidPasswordError) as error:
            password_policy.validate("Long password 123")

        assert error.value.details["reason"] == "no_special_character"
