import tomllib
from pathlib import Path


class TestPyProjectToml:
    def test_exists(self):
        assert Path("pyproject.toml").is_file()

    def test_click_dependency(self):
        data = tomllib.loads(Path("pyproject.toml").read_text())
        deps = data["project"]["dependencies"]
        assert any(dep.startswith("click") for dep in deps)

    def test_console_scripts_entry_point(self):
        data = tomllib.loads(Path("pyproject.toml").read_text())
        scripts = data["project"]["scripts"]
        assert scripts["gitnotes"] == "gitnotes.cli:main"
