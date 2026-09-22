import pytest

from src.domain.enums.account_status import AccountStatus


class TestAccountStatusValues:
    @pytest.mark.parametrize(
        "member, expected_value",
        [
            (AccountStatus.ACTIVE, "active"),
            (AccountStatus.DISABLED, "disabled"),
            (AccountStatus.DELETED, "deleted"),
        ],
    )
    def test_value_matches_lowercase_name(self, member: AccountStatus, expected_value: str):
        assert member.value == expected_value
        assert str(member) == expected_value

    def test_is_str_subclass(self):
        assert isinstance(AccountStatus.ACTIVE, str)

    def test_can_be_constructed_from_raw_string(self):
        assert AccountStatus("active") is AccountStatus.ACTIVE

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            AccountStatus("suspended")

    def test_all_members_present(self):
        assert {member.value for member in AccountStatus} == {
            "active",
            "disabled",
            "deleted",
        }
