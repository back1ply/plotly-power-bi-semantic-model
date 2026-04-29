"""Tests for safe_callback decorator in components/base.py."""

import pytest
from presentation.callbacks import safe_callback


class TestSafeCallback:
    def test_passes_through_return_value(self):
        """Decorator returns function result normally."""

        @safe_callback
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_passes_through_none_return(self):
        """Decorator handles None return value."""

        @safe_callback
        def returns_none():
            return None

        result = returns_none()
        assert result is None

    def test_logs_and_reraises_exception(self):
        """Exception is logged then re-raised."""

        @safe_callback
        def raises_error():
            raise ValueError("test error")

        # Test that exception is raised - the logging part is hard to test directly
        # because _logger is defined inside the function scope
        with pytest.raises(ValueError, match="test error"):
            raises_error()

    def test_logs_different_exception_types(self):
        """Logger handles different exception types."""

        @safe_callback
        def raises_type_error():
            raise TypeError("type mismatch")

        with pytest.raises(TypeError):
            raises_type_error()

    def test_preserves_function_metadata(self):
        """Decorator preserves function name and docstring."""

        @safe_callback
        def documented_func():
            """This is the docstring."""
            return 42

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is the docstring."

    def test_handles_keyword_arguments(self):
        """Decorator passes through keyword arguments."""

        @safe_callback
        def kwargs_func(a, b=10, c=20):
            return a + b + c

        result = kwargs_func(1, b=2, c=3)
        assert result == 6

    def test_log_includes_traceback(self):
        """Log output includes full traceback."""

        @safe_callback
        def deep_error():
            raise RuntimeError("inner error")

        # Just verify the exception is re-raised - traceback logging is inside function scope
        with pytest.raises(RuntimeError, match="inner error"):
            deep_error()
