import pytest

from seer_pas_sdk.auth import Auth


@pytest.fixture
def password():
    return "XXX_fake_password"


@pytest.fixture
def username():
    return "XXX_fake_user"


@pytest.fixture(
    params=[
        *Auth._instances.keys(),
        *Auth._instances.values(),
        "https://secure-https-url.example/",
    ]
)
def valid_instance(request):
    return request.param


def test_valid_instance(username, password, valid_instance):
    Auth(
        username=username,
        password=password,
        instance=valid_instance,
    )


@pytest.fixture(
    params=[
        "XX",
        # "http://insecure-http-url.example/",  # Currently permitted (to support dev instance)
        "my-favorite-instance",
    ]
)
def invalid_instance(request):
    return request.param


def test_invalid_instance(username, password, invalid_instance):
    with pytest.raises(ValueError):
        Auth(
            username=username,
            password=password,
            instance=invalid_instance,
        )
