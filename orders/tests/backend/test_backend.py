import json

import pytest
from backend.models import *
from rest_framework.authtoken.models import Token


@pytest.mark.django_db
def test_user_registration(client, user_info):
    url = 'http://127.0.0.1:8000/user/register'
    response = client.post(url, data=user_info)
    assert response.status_code == 201


@pytest.mark.django_db
def test_user_reg_common_password(client, user_info):
    url = 'http://127.0.0.1:8000/user/register'
    user_info.update({'password': '123'})
    response = client.post(url, data=user_info)
    assert response.status_code == 403
    assert response.json()['Errors']['password'][1] == 'This password is too common.'


@pytest.mark.django_db
def test_user_reg_less_arg(client, user_info):
    url = 'http://127.0.0.1:8000/user/register'
    user_info.pop('first_name')
    response = client.post(url, data=user_info)
    assert response.status_code == 400
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_user_confirm(client, user_factory):
    url = 'http://127.0.0.1:8000/user/register/confirm'
    user = user_factory(_quantity=1)
    token = ConfirmEmailToken.objects.create(user=user[0])
    response = client.post(url, data={'email': user[0].email, 'token': token.key})
    assert response.status_code == 201
    assert response.json()['Status'] == True


@pytest.mark.django_db
def test_user_conf_wrong_email(client, user_factory):
    url = 'http://127.0.0.1:8000/user/register/confirm'
    user = user_factory(_quantity=1)
    token = ConfirmEmailToken.objects.create(user=user[0])
    response = client.post(url, data={'email': 'email@email.com', 'token': token.key})
    assert response.status_code == 403
    assert response.json()['Error'] == 'Неправильно указан токен или email'


@pytest.mark.django_db
def test_user_conf_less_arg(client, user_factory):
    url = 'http://127.0.0.1:8000/user/register/confirm'
    user = user_factory(_quantity=1)
    token = ConfirmEmailToken.objects.create(user=user[0])
    response = client.post(url, data={'token': token.key})
    assert response.status_code == 403
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_user_login(client, user_factory):
    url = 'http://127.0.0.1:8000/user/login'
    test_user = user_factory(_quantity=1, is_active=True)
    test_user[0].set_password('1q2w3e4r5!@')
    test_user[0].save()
    response = client.post(url, data={'email': test_user[0].email, 'password': '1q2w3e4r5!@'})
    assert response.status_code == 201
    token = Token.objects.get(user=test_user[0].id).key
    assert response.json()['Token'] == token


@pytest.mark.django_db
def test_user_login_wrong_email(client, user_factory):
    url = 'http://127.0.0.1:8000/user/login'
    test_user = user_factory(_quantity=1, is_active=True)
    test_user[0].set_password('1q2w3e4r5!@')
    test_user[0].save()
    response = client.post(url, data={'email': 'email@email.com', 'password': '1q2w3e4r5!@'})
    assert response.status_code == 401
    assert response.json()['Error'] == 'Не удалось авторизовать'


@pytest.mark.django_db
def test_user_login_wrong_email(client, user_factory):
    url = 'http://127.0.0.1:8000/user/login'
    test_user = user_factory(_quantity=1, is_active=True)
    test_user[0].set_password('1q2w3e4r5!@')
    test_user[0].save()
    response = client.post(url, data={'password': '1q2w3e4r5!@'})
    assert response.status_code == 403
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_get_user_info(client, seller_token):
    url = 'http://127.0.0.1:8000/user/info'
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()['email'] == 'seller@example.com'


@pytest.mark.django_db
def test_get_user_info_no_auth(client):
    url = 'http://127.0.0.1:8000/user/info'
    response = client.get(url)
    assert response.status_code == 403
    assert response.json()['Error'] == 'Log in required'


@pytest.mark.django_db
def test_user_change_password(client, seller_token):
    url = 'http://127.0.0.1:8000/user/info'
    response = client.post(url, data={'password': '!Q@W#E$R%T^T12'})
    assert response.status_code == 201
    assert response.json()['Status'] == True
    password = User.objects.get(email='seller@example.com').password
    assert password == '!Q@W#E$R%T^T12'


@pytest.mark.django_db
def test_user_chg_pass_less_args(client, seller_token):
    url = 'http://127.0.0.1:8000/user/info'
    response = client.post(url)
    assert response.status_code == 403
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_user_chg_pass_no_auth(client):
    url = 'http://127.0.0.1:8000/user/info'
    response = client.post(url, data={'password': '!Q@W#E$R%T^T12'})
    assert response.status_code == 403
    assert response.json()['Error'] == 'Log in required'


@pytest.mark.django_db
def test_user_chg_pass_common(client, seller_token):
    url = 'http://127.0.0.1:8000/user/info'
    response = client.post(url, data={'password': '123'})
    assert response.status_code == 400
    assert response.json()['Errors']['password'][0] == 'This password is too short. ' \
                                                       'It must contain at least 8 characters.'


@pytest.mark.django_db
def test_get_user_info(client, seller_token):
    url = 'http://127.0.0.1:8000/user/contact'
    data = {
        "country": "Russia",
        "region": "Moscow",
        "zip": 628000,
        "city": "Moscow",
        "street": "Lenin",
        "house": "21",
        "phone": "+79000000000"
    }
    response = client.post(url, data=data)
    assert response.status_code == 200
    assert response.json()['Status'] == True
