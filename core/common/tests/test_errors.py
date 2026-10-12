from fource.common import FourceError


class Teapot(FourceError):
    code = "teapot"
    status = 418


def test_an_error_carries_its_code_status_and_message() -> None:
    error = Teapot("Short and stout.")
    assert (error.code, error.status, error.message) == ("teapot", 418, "Short and stout.")
    assert str(error) == "Short and stout."


def test_the_base_error_is_a_server_error() -> None:
    assert (FourceError.code, FourceError.status) == ("error", 500)
