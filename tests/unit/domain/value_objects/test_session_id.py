from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from src.domain.value_objects import SessionId


class TestSessionId:

    def test_stores_uuid_value(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        session_id = SessionId(value=value)
        assert session_id.value == value

    def test_converts_to_string(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        session_id = SessionId(value=value)
        assert str(session_id) == str(value)

    def test_with_same_value_is_equal(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        session_id_1 = SessionId(value=value)
        session_id_2 = SessionId(value=value)
        assert session_id_1 == session_id_2

    def test_with_different_value_is_not_equal(self):
        session_id_1 = SessionId(value=UUID("12345678-1234-5678-1234-567812345678"))
        session_id_2 = SessionId(value=UUID("22345678-1234-5678-1234-567812345678"))
        assert session_id_1 != session_id_2

    def test_does_not_allow_new_attributes(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        session_id = SessionId(value=value)
        with pytest.raises(TypeError):
            session_id.new_attribute = "new_value"

    def test_is_immutable(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        session_id = SessionId(value=value)
        with pytest.raises(FrozenInstanceError):
            session_id.value = UUID("22345678-1234-5678-1234-567812345678")

    def test_session_id_rejects_non_uuid_value(self):
        with pytest.raises(TypeError, match="SessionId.value must be UUID"):
            SessionId(value="12345678-1234-5678-1234-567812345678")

    def test_rejects_none_value(self):
        with pytest.raises(TypeError, match="SessionId.value must be UUID"):
            SessionId(value=None)
