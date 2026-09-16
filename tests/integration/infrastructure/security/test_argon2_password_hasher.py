from src.infrastructure.security import Argon2PasswordHasher


class TestArgon2PasswordHasher:
    def test_hash_returns_different_value_than_raw_password(self) -> None:
        hasher = Argon2PasswordHasher()
        raw_password = "StrongPassword123!"

        password_hash = hasher.hash(raw_password)

        assert password_hash.value != raw_password
        assert password_hash.value.startswith("$argon2")

    def test_verify_returns_true_for_correct_password(self) -> None:
        hasher = Argon2PasswordHasher()
        raw_password = "StrongPassword123!"

        password_hash = hasher.hash(raw_password)

        assert hasher.verify(raw_password, password_hash) is True

    def test_verify_returns_false_for_wrong_password(self) -> None:
        hasher = Argon2PasswordHasher()
        password_hash = hasher.hash("StrongPassword123!")

        result = hasher.verify(
            "WrongPassword123!",
            password_hash,
        )

        assert result is False

    def test_hashes_same_password_to_different_hashes(self) -> None:
        hasher = Argon2PasswordHasher()
        raw_password = "StrongPassword123!"

        first_hash = hasher.hash(raw_password)
        second_hash = hasher.hash(raw_password)

        assert first_hash != second_hash
        assert hasher.verify(raw_password, first_hash) is True
        assert hasher.verify(raw_password, second_hash) is True