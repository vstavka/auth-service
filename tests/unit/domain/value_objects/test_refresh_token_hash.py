from dataclasses import FrozenInstanceError

import pytest

from src.domain.value_objects import RefreshTokenHash


class TestRefreshTokenHash:

    def test_stores_value(self):
        value = "a" * 64
        refresh_token_hash = RefreshTokenHash(value=value)
        assert refresh_token_hash.value == value

    def test_converts_to_string(self):
        value = "a" * 64
        refresh_token_hash = RefreshTokenHash(value=value)
        assert str(refresh_token_hash) == str(value)

    def test_with_same_value_is_equal(self):
        value = "a" * 64
        refresh_token_hash_1 = RefreshTokenHash(value=value)
        refresh_token_hash_2 = RefreshTokenHash(value=value)
        assert refresh_token_hash_1 == refresh_token_hash_2

    def test_with_different_value_is_not_equal(self):
        refresh_token_hash_1 = RefreshTokenHash(value="a" * 64)
        refresh_token_hash_2 = RefreshTokenHash(value="b" * 64)
        assert refresh_token_hash_1 != refresh_token_hash_2

    def test_does_not_allow_new_attributes(self):
        value = "a" * 64
        refresh_token_hash = RefreshTokenHash(value=value)
        with pytest.raises(TypeError):
            refresh_token_hash.new_attribute = "new_value"

    def test_is_immutable(self):
        value = "a" * 64
        refresh_token_hash = RefreshTokenHash(value=value)
        with pytest.raises(FrozenInstanceError):
            refresh_token_hash.value = "b" * 64

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError, match="RefreshTokenHash.value must not be empty"):
            RefreshTokenHash("")

    def test_rejects_non_str_value(self):
        with pytest.raises(TypeError, match="RefreshTokenHash.value must be str"):
            RefreshTokenHash(value=None)
