from app.utils.id_generator import ALPHABET, generate_short_code


def test_generate_short_code_default_length() -> None:
    code = generate_short_code()
    assert len(code) == 8
    assert all(char in ALPHABET for char in code)


def test_generate_short_code_custom_length() -> None:
    length = 12
    code = generate_short_code(length)
    assert len(code) == length


def test_generate_short_code_rejects_short_length() -> None:
    try:
        generate_short_code(3)
    except ValueError as exc:
        assert "at least 4" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("Expected ValueError for short length")
