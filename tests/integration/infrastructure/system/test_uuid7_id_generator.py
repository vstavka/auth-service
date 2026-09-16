from uuid import UUID

from src.infrastructure.system import UUID7IdGenerator


class TestUUID7IdGenerator:
    def test_generates_uuid_instance(self) -> None:
        generator = UUID7IdGenerator()

        generated_id = generator.new()

        assert isinstance(generated_id, UUID)

    def test_generates_uuid_version_7(self) -> None:
        generator = UUID7IdGenerator()

        generated_id = generator.new()

        assert generated_id.version == 7

    def test_generates_unique_values(self) -> None:
        generator = UUID7IdGenerator()

        first_id = generator.new()
        second_id = generator.new()

        assert first_id != second_id

    def test_generated_uuids_are_time_ordered(self) -> None:
        generator = UUID7IdGenerator()

        generated_ids = [
            generator.new()
            for _ in range(100)
        ]

        assert generated_ids == sorted(generated_ids)
