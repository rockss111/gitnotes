"""
Unit Tests: Isolated component testing

Per ADR 0014 (Testability): Unit tests for isolated components like hashing,
config resolution, and lock management.
"""

import os


class TestConfigResolver:
    """Unit tests: Editor configuration resolution."""

    def test_fallback_precedence(self):
        """Test that fallback chain works in correct order."""
        from src.gitnotes.config_resolver import resolve_editor, _get_env_var_fallbacks

        # Clear any existing env vars to force fallback
        original_visual = os.environ.pop("VISUAL", None)
        original_editor = os.environ.pop("EDITOR", None)

        try:
            fallbacks = _get_env_var_fallbacks()
            assert len(fallbacks) == 2, "Should have exactly 2 fallbacks"
            assert fallbacks[0][0] == "VISUAL", "First fallback should be VISUAL"
            assert fallbacks[1][0] == "EDITOR", "Second fallback should be EDITOR"
        finally:
            # Restore
            if original_visual is not None:
                os.environ["VISUAL"] = original_visual
            elif "VISUAL" in os.environ:
                del os.environ["VISUAL"]

            if original_editor is not None:
                os.environ["EDITOR"] = original_editor
            elif "EDITOR" in os.environ:
                del os.environ["EDITOR"]

        # Test VISUAL fallback
        os.environ["VISUAL"] = "vim"
        assert resolve_editor() == "vim", "Should return VISUAL when set"

        # Clean up
        if "VISUAL" in os.environ:
            del os.environ["VISUAL"]

    def test_empty_config_returns_fallbacks(self):
        """Test that empty config file still checks env vars."""
        from src.gitnotes.config_resolver import resolve_editor

        # Simulate empty/missing project config
        os.environ["VISUAL"] = "nano"
        result = resolve_editor()
        assert result == "nano", "Should fall through to VISUAL when config is empty"

        if "VISUAL" in os.environ:
            del os.environ["VISUAL"]
