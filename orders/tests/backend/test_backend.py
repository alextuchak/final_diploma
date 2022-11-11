from orders.settings import BASE_DIR
from django.test.client import encode_multipart
import pytest
from backend.models import *
from rest_framework.authtoken.models import Token
import os
from mock import patch


@pytest.mark.django_db
def test_user_registration(client, user_info, ):
    with patch('backend.tasks.new_user_registered_task') as mock_task:
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
    with patch('backend.tasks.handle_uploaded_file_task') as mock_task:
        url = 'http://127.0.0.1:8000/shop/upload'
        data = {'file': ('shop1.yaml', open(os.path.join(BASE_DIR + '/data/shop1.yaml')), 'rb')}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
        response = client.post(url, content, content_type=content_type)
        assert response.status_code == 201


@pytest.mark.django_db
def test_shop_inf_upload_no_auth(client):
    with patch('backend.tasks.handle_uploaded_file_task') as mock_task:
        url = 'http://127.0.0.1:8000/shop/upload'
        data = {'file': ('shop1.yaml', open(os.path.join(BASE_DIR + '/data/shop1.yaml')), 'rb')}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
        response = client.post(url, content, content_type=content_type)
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Error'] == 'Log in required'


@pytest.mark.django_db
def test_shop_inf_upload_buyer(client, buyer_token):
    with patch('backend.tasks.handle_uploaded_file_task') as mock_task:
        url = 'http://127.0.0.1:8000/shop/upload'
        data = {'file': ('shop1.yaml', open(os.path.join(BASE_DIR + '/data/shop1.yaml')), 'rb')}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
        response = client.post(url, content, content_type=content_type)
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Error'] == 'Только для магазинов'


@pytest.mark.django_db
def test_shop_inf_upload_wrong_arg(client, seller_token):
    with patch('backend.tasks.handle_uploaded_file_task') as mock_task:
        url = 'http://127.0.0.1:8000/shop/upload'
        data = {'yaml': ('shop1.yaml', open(os.path.join(BASE_DIR + '/data/shop1.yaml')), 'rb')}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
        response = client.post(url, content, content_type=content_type)
        assert response.status_code == 400
        assert response.json()['Status'] == False


@pytest.mark.django_db
def test_basket_post(client, buyer_token, shops_create):
    data = [{"product_info": shops_create, "quantity": 4}]
    url = 'http://127.0.0.1:8000/basket/'
    response = client.post(url, data=data)
    assert response.status_code == 201


@pytest.mark.django_db
def test_basket_post_no_auth(client, shops_create):
    data = [{"product_info": shops_create, "quantity": 4}]
    url = 'http://127.0.0.1:8000/basket/'
    response = client.post(url, data=data)
    assert response.status_code == 401
    assert response.json()['detail'] == 'Authentication credentials were not provided.'


@pytest.mark.django_db
def test_basket_post_wrong_arg(client, buyer_token, shops_create):
    data = [{"product_info": 27, "quantity": 4}]
    url = 'http://127.0.0.1:8000/basket/'
    response = client.post(url, data=data)
    assert response.status_code == 400
    assert response.json()['Возникла ошибка!']['product_info'][0] == 'Invalid pk "27" - object does not exist.'


@pytest.mark.django_db
def test_basket_post_no_data(client, buyer_token, shops_create):
    url = 'http://127.0.0.1:8000/basket/'
    response = client.post(url,)
    assert response.status_code == 403
    assert response.json()['Status'] == False
    assert response.json()['Возникла ошибка!'] == 'Указаны не все аргументы'


@pytest.mark.django_db
def test_basket_get(client, buyer_token, basket_create):
    url = 'http://127.0.0.1:8000/basket/'
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()[0]['total_sum'] == 400000


@pytest.mark.django_db
def test_basket_put(client, buyer_token, basket_create):
    data = [{"product_info": basket_create[0], "quantity": 7}]
    url = 'http://127.0.0.1:8000/basket/'
    response = client.put(url, data=data)
    assert response.status_code == 200
    assert response.json()['Status'] == True
    ordered_items = OrderItem.objects.filter(id=basket_create[1]).first()
    assert data[0]['quantity'] == ordered_items.quantity


@pytest.mark.django_db
def test_basket_put_no_data(client, buyer_token, basket_create):
    url = 'http://127.0.0.1:8000/basket/'
    response = client.put(url,)
    assert response.status_code == 403
    assert response.json()['Status'] == False
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_basket_put_wrong_args(client, buyer_token, basket_create):
    data = [{"quantity": 7}]
    url = 'http://127.0.0.1:8000/basket/'
    response = client.put(url, data=data)
    assert response.status_code == 403
    assert response.json()['Возникла ошибка!']['product_info'][0] == 'This field is required.'


@pytest.mark.django_db
def test_basket_delete(client, buyer_token, basket_create):
    url = 'http://127.0.0.1:8000/basket/'
    data = {'items': basket_create[0]}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.delete(url, content, content_type=content_type)
    print(response.json())
    assert response.status_code == 200
    basket = OrderItem.objects.all()
    assert len(basket) == 0


@pytest.mark.django_db
def test_basket_delete_wrong_arg(client, buyer_token, basket_create):
    url = 'http://127.0.0.1:8000/basket/'
    data = {'items': 5555}
    content = encode_multipart('BoUnDaRyStRiNg', data)
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    response = client.delete(url, content, content_type=content_type)
    assert response.status_code == 403
    assert response.json()['Status'] == False
    assert response.json()['Error'] == 'Укажите корректные товары для удаления'


@pytest.mark.django_db
def test_basket_delete_no_arg(client, buyer_token, basket_create):
    url = 'http://127.0.0.1:8000/basket/'
    response = client.delete(url,)
    assert response.status_code == 403
    assert response.json()['Status'] == False
    assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_order_create(client, buyer_token, basket_create):
    with patch('backend.tasks.new_order_task') as mock_task1:
        with patch('backend.tasks.new_order_for_seller_task') as mock_task2:
            url = 'http://127.0.0.1:8000/order/customer/'
            data = {'id': basket_create[2]}
            content = encode_multipart('BoUnDaRyStRiNg', data)
            content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
            response = client.post(url, content, content_type=content_type)
            assert response.status_code == 201


@pytest.mark.django_db
def test_order_create_without_contact(client, buyer_token, basket_create):
    with patch('backend.tasks.new_order_task') as mock_task1:
        with patch('backend.tasks.new_order_for_seller_task') as mock_task2:
            cotact = Contact.objects.filter(user=basket_create[3]).delete()
            url = 'http://127.0.0.1:8000/order/customer/'
            data = {'id': basket_create[2]}
            content = encode_multipart('BoUnDaRyStRiNg', data)
            content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
            response = client.post(url, content, content_type=content_type)
            assert response.status_code == 403
            assert response.json()['Error'] == 'Не указаны контакты для связи'


@pytest.mark.django_db
def test_order_create_no_data(client, buyer_token, basket_create):
    with patch('backend.tasks.new_order_task') as mock_task1:
        with patch('backend.tasks.new_order_for_seller_task') as mock_task2:
            url = 'http://127.0.0.1:8000/order/customer/'
            response = client.post(url,)
            assert response.status_code == 403
            assert response.json()['Error'] == 'Не указаны все необходимые аргументы'


@pytest.mark.django_db
def test_order_get_by_seller(client, order_create):
    url = 'http://127.0.0.1:8000/order/seller/'
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()[0]['total_sum'] == 400000
    assert response.json()[0]['status'] == "new"


@pytest.mark.django_db
def test_order_put_by_seller(client, order_create):
    with patch('backend.tasks.order_status_change_task') as mock_task:
        url = 'http://127.0.0.1:8000/order/seller/'
        data = {"id": order_create[1], "status": "confirmed"}
        response = client.put(url, data)
        assert response.status_code == 201
        assert response.json()["Статус заказа обновлен"] == data['status']


@pytest.mark.django_db
def test_order_put_by_seller_wrong_data(client, order_create):
    with patch('backend.tasks.order_status_change_task') as mock_task:
        url = 'http://127.0.0.1:8000/order/seller/'
        data = {"id": order_create[1],}
        response = client.put(url, data)
        assert response.status_code == 403
        assert response.json()['Возникла ошибка!'] == "Некоректный формат данных"


@pytest.mark.django_db
def test_order_put_by_buyer(client, order_create):
    with patch('backend.tasks.order_status_change_task') as mock_task:
        url = 'http://127.0.0.1:8000/order/seller/'
        data = {"id": order_create[1], "status": "confirmed"}
        client.credentials(HTTP_AUTHORIZATION=f'Token {order_create[2]}')
        response = client.put(url, data,)
        assert response.status_code == 403
        assert response.json()['Error'] == 'Только для магазинов'



