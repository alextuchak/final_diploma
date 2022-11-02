import pytest
from model_bakery import baker
from backend.models import *
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_factory():
    def factory(*args, **kwargs):
        return baker.make(User, *args, **kwargs)

    return factory


@pytest.fixture
def user_info():
    return {"first_name": "seller", "last_name": "seller", "email": "seller@example.com", "password": "1q2w3e4r5!@",
            "type": "seller"}


@pytest.fixture
def seller_token(client):
    user = User.objects.create_user(email='seller@example.com', password='1q2w3e4r5!@', first_name='seller',
                                    username='seller', last_name='seller', is_active=True, type='seller')
    token = Token.objects.create(user=user)
    return client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
