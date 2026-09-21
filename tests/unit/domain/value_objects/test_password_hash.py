from dataclasses import FrozenInstanceError

import pytest

from src.domain.value_objects import PasswordHash


class TestPasswordHash:

    def test_stores_uuid_value(self):
        value = "e99a18exampleExampleExampleExampleExampleExampleExample"
        password_hash = PasswordHash(value=value)
        assert password_hash.value == value

    def test_converts_to_string(self):
        value = "e99a18exampleExampleExampleExampleExampleExampleExample"
        password_hash = PasswordHash(value=value)
        assert str(password_hash) == str(value)

    def test_with_same_value_is_equal(self):
        value = "e99a18exampleExampleExampleExampleExampleExampleExample"
        password_hash_1 = PasswordHash(value=value)
        password_hash_2 = PasswordHash(value=value)
        assert password_hash_1 == password_hash_2

    def test_with_different_value_is_not_equal(self):
        password_hash_1 = PasswordHash(value="e99a18exampleExampleExampleExampleExampleExampleExample")
        password_hash_2 = PasswordHash(value="e99a20exampleExampleExampleExampleExampleExampleExample")
        assert password_hash_1 != password_hash_2

    def test_does_not_allow_new_attributes(self):
        value = "e99a18exampleExampleExampleExampleExampleExampleExample"
        password_hash = PasswordHash(value=value)
        with pytest.raises(TypeError):
            password_hash.new_attribute = "new_value"

    def test_is_immutable(self):
        value = "e99a18exampleExampleExampleExampleExampleExampleExample"
        password_hash = PasswordHash(value=value)
        with pytest.raises(FrozenInstanceError):
            password_hash.value = "e99a20exampleExampleExampleExampleExampleExampleExample"

    def test_accepts_empty_string(self):
        password_hash = PasswordHash("")

        assert password_hash.value == ""
