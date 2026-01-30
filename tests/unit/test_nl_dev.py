import pytest

# CodeGenerator pending migration from legacy_src/
CodeGenerator = None


@pytest.mark.skipif(CodeGenerator is None, reason="CodeGenerator pending migration")
class TestCodeGenerator:
    @pytest.fixture
    def generator(self):
        return CodeGenerator()

    def test_generate_modify_file_success(self, generator, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("initial")

        result = generator.generate_modify_file(str(f), ["line1", "line2"])

        assert result.success
        assert str(f) in result.files_modified
        assert f.read_text() == "initial\nline1\nline2"

    def test_generate_delete_file_success(self, generator, tmp_path):
        f = tmp_path / "to_delete.txt"
        f.write_text("content")

        result = generator.generate_delete_file(str(f))

        assert result.success
        assert str(f) in result.files_modified
        assert not f.exists()

    def test_modify_file_not_found(self, generator):
        result = generator.generate_modify_file("nonexistent.txt", ["change"])
        assert not result.success
        assert "File not found" in result.errors[0]

    def test_delete_file_not_found(self, generator):
        result = generator.generate_delete_file("nonexistent.txt")
        assert not result.success
        assert "File not found" in result.errors[0]
