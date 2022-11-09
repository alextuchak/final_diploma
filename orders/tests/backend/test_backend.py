from orders.settings import BASE_DIR
from django.test.client import encode_multipart
import pytest
from backend.models import *
from rest_framework.authtoken.models import Token
import os


@pytest.mark.django_db
def test_user_registration(client, user_info, ):
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
def test_user_confirm(client, user_create):
    url = 'http://127.0.0.1:8000/user/register/confirm'
    token = ConfirmEmailToken.objects.create(user=user_create)
    response = client.post(url, data={'email': user_create.email, 'token': token.key})
    assert response.status_code == 201
    assert response.json()['Status'] == True


@pytest.mark.django_db
def test_user_conf_wrong_email(client, user_create):
    url = 'http://127.0.0.1:8000/user/register/confirm'
    token = ConfirmEmailToken.objects.create(user=user_create)
    response = client.post(url, data={'email': 'email@email.com', 'token': token.key})
    assert response.status_code == 403
    assert response.json()['Error'] == 'Неправильно указан токен или email'


@pytest.mark.django_db
def test_user_conf_less_arg(client, user_create):
    url = 'http://127.0.0.1:8000/user/register/confirm'
    token = ConfirmEmailToken.objects.create(user=user_create)
    response = client.post(url, data={'token': token.key})
    assert response.status_code == 403
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_user_login(client, user_create, user_info):
    url = 'http://127.0.0.1:8000/user/login'
    response = client.post(url, data={'email': user_create.email, 'password': user_info['password']})
    assert response.status_code == 201
    token = Token.objects.get(user=user_create.id).key
    assert response.json()['Token'] == token


@pytest.mark.django_db
def test_user_login_wrong_email(client, user_create, user_info):
    url = 'http://127.0.0.1:8000/user/login'
    response = client.post(url, data={'email': 'email@email.com', 'password': user_info['password']})
    assert response.status_code == 401
    assert response.json()['Error'] == 'Не удалось авторизовать'


@pytest.mark.django_db
def test_user_login_less_arg(client, user_create, user_info):
    url = 'http://127.0.0.1:8000/user/login'
    response = client.post(url, data={'password': user_info['password']})
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
def test_user_change_password(client, seller_token, user_info):
    url = 'http://127.0.0.1:8000/user/info'
    response = client.post(url, data={'password': '!Q@W#E$R%T^T12'})
    assert response.status_code == 201
    assert response.json()['Status'] == True
    password = User.objects.get(email=user_info['email']).password
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
def test_post_user_contact(client, seller_token, users_contact_data):
    url = 'http://127.0.0.1:8000/user/contact'
    response = client.post(url, data=users_contact_data)
    assert response.status_code == 201
    assert response.json()['Status'] == True


@pytest.mark.django_db
def test_post_user_contact_no_auth(client, users_contact_data):
    url = 'http://127.0.0.1:8000/user/contact'
    response = client.post(url, data=users_contact_data)
    assert response.status_code == 403
    assert response.json()['Error'] == 'Log in required'


@pytest.mark.django_db
def test_post_user_contact_less_arg(client, seller_token, users_contact_data):
    url = 'http://127.0.0.1:8000/user/contact'
    users_contact_data.pop('country')
    response = client.post(url, data=users_contact_data)
    assert response.status_code == 403
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_post_user_contact_wrong_phone(client, seller_token, users_contact_data):
    url = 'http://127.0.0.1:8000/user/contact'
    users_contact_data.update({'phone': 1})
    response = client.post(url, data=users_contact_data)
    assert response.status_code == 400
    assert response.json()['Errors']['Error'][0] == "Некорректный формат номера"


@pytest.mark.django_db
def test_del_contact(client, seller_token, contact_factory, user_create):
    url = 'http://127.0.0.1:8000/user/contact'
    contact = contact_factory(user=user_create, _quantity=1)
    data = {'items': contact[0].id}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.delete(url, content, content_type=content_type)
    assert response.status_code == 200
    assert response.json()['Status'] == True
    assert response.json()['Удалено объектов'] == 1


@pytest.mark.django_db
def test_del_contact_no_auth(client, contact_factory, user_create):
    url = 'http://127.0.0.1:8000/user/contact'
    contact = contact_factory(user=user_create, _quantity=1)
    data = {'items': contact[0].id}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.delete(url, content, content_type=content_type)
    assert response.status_code == 403
    assert response.json()['Status'] == False
    assert response.json()['Error'] == 'Log in required'


@pytest.mark.django_db
def test_del_contact_no_content(client, seller_token, contact_factory, user_create):
    url = 'http://127.0.0.1:8000/user/contact'
    contact = contact_factory(user=user_create, _quantity=1)
    data = {}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.delete(url, content, content_type=content_type)
    assert response.status_code == 403
    assert response.json()['Status'] == False
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_put_contact(client, seller_token, contact_factory, user_create):
    url = 'http://127.0.0.1:8000/user/contact'
    contact = contact_factory(user=user_create, phone=89228888888, _quantity=1)
    data = {'id': contact[0].id, 'phone': '79999999999'}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.put(url, content, content_type=content_type)
    assert response.status_code == 201
    new_contact = Contact.objects.get(user=user_create.id)
    assert new_contact.phone == data['phone']


@pytest.mark.django_db
def test_put_contact_no_auth(client, contact_factory, user_create):
    url = 'http://127.0.0.1:8000/user/contact'
    contact = contact_factory(user=user_create, phone=89228888888, _quantity=1)
    data = {'id': contact[0].id, 'phone': '79999999999'}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.put(url, content, content_type=content_type)
    assert response.status_code == 403
    assert response.json()['Status'] == False
    assert response.json()['Error'] == 'Log in required'


@pytest.mark.django_db
def test_put_contact_less_arg(client, seller_token, contact_factory, user_create):
    url = 'http://127.0.0.1:8000/user/contact'
    contact = contact_factory(user=user_create, phone=89228888888, _quantity=1)
    data = {'phone': '79999999999'}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.put(url, content, content_type=content_type)
    assert response.status_code == 403
    assert response.json()['Status'] == False
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_put_contact_less_arg(client, seller_token, contact_factory, user_create):
    url = 'http://127.0.0.1:8000/user/contact'
    contact = contact_factory(user=user_create, phone=9, _quantity=1)
    data = {'id': contact[0].id, 'phone': '9'}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.put(url, content, content_type=content_type)
    assert response.status_code == 400
    assert response.json()['Errors']['Error'][0] == "Некорректный формат номера"


@pytest.mark.django_db
def test_get_categeroies(client, categories_factory):
    url = 'http://127.0.0.1:8000/categories/'
    categories = categories_factory(_quantity=3)
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.django_db
def test_get_products(client, products_create):
    url = 'http://127.0.0.1:8000/products/'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 10


@pytest.mark.django_db
def test_get_products_inf(client, products_create):
    url = 'http://127.0.0.1:8000/product_inf/'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 50


@pytest.mark.django_db
def test_get_shops(client, shops_create):
    url = 'http://127.0.0.1:8000/shops/'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.django_db
def test_get_products_in_shop(client, shops_create):
    url = 'http://127.0.0.1:8000/products_in_shop/'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.django_db
def test_shop_inf_upload(client, seller_token):
    url = 'http://127.0.0.1:8000/shop/upload'
    data = {'file': ('shop1.yaml', open(os.path.join(BASE_DIR + '/data/shop1.yaml')), 'rb')}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.post(url, content, content_type=content_type)
    print(response.json())
    assert response.status_code == 201





