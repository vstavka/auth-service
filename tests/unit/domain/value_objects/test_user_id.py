from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from src.domain.value_objects import UserId


class TestUserId:

    def test_stores_uuid_value(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UserId(value=value)
        assert user_id.value == value

    def test_converts_to_string(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UserId(value=value)
        assert str(user_id) == str(value)

    def test_with_same_value_is_equal(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        user_id_1 = UserId(value=value)
        user_id_2 = UserId(value=value)
        assert user_id_1 == user_id_2

    def test_with_different_value_is_not_equal(self):
        user_id_1 = UserId(value=UUID("12345678-1234-5678-1234-567812345678"))
        user_id_2 = UserId(value=UUID("22345678-1234-5678-1234-567812345678"))
        assert user_id_1 != user_id_2

    def test_does_not_allow_new_attributes(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UserId(value=value)
        with pytest.raises(TypeError):
            user_id.new_attribute = "new_value"

    def test_is_immutable(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UserId(value=value)
        with pytest.raises(FrozenInstanceError):
            user_id.value = UUID("22345678-1234-5678-1234-567812345678")

    def test_user_id_rejects_non_uuid_value(self):
        with pytest.raises(TypeError, match="UserId.value must be UUID"):
            UserId(value="12345678-1234-5678-1234-567812345678")

    def test_rejects_none_value(self):
        with pytest.raises(TypeError, match="UserId.value must be UUID"):
            UserId(value=None)
