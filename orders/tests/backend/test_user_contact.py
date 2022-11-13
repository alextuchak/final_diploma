import pytest
from django.test.client import encode_multipart
from backend.models import *


@pytest.mark.django_db
class TestUserContact:
    """
    Класс для тестирования UserContact
    """
    url = 'http://127.0.0.1:8000/user/contact'
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

    def test_post_user_contact(self, client, seller_token, users_contact_data):
        """
         Тест на создание контактов пользователя
         Ожидаемый результат - подтверждение создания контактов
        """

        response = client.post(self.url, data=users_contact_data)
        assert response.status_code == 201
        assert response.json()['Status'] == True

    def test_post_user_contact_no_auth(self, client, users_contact_data):
        """
        Тест на создание контактов пользователя без аутентификации
        Ожидаемый результат - ошибка
        """

        response = client.post(self.url, data=users_contact_data)
        assert response.status_code == 403
        assert response.json()['Error'] == 'Log in required'

    def test_post_user_contact_less_arg(self, client, seller_token, users_contact_data):
        """
        Тест на создание контактов пользователя без указания всех необходимых аргументов
        Ожидаемый результат - ошибка
        """

        users_contact_data.pop('country')
        response = client.post(self.url, data=users_contact_data)
        assert response.status_code == 403
        assert response.json()['Error'] == 'Не указаны все необходимые аргументы'

    def test_post_user_contact_wrong_phone(self, client, seller_token, users_contact_data):
        """
        Тест на создание контактов пользователя с указанием некорректного номера телефона
        Ожидаемый результат - ошибка
        """

        users_contact_data.update({'phone': 1})
        response = client.post(self.url, data=users_contact_data)
        assert response.status_code == 400
        assert response.json()['Errors']['Error'][0] == "Некорректный формат номера"

    def test_del_contact(self, client, seller_token, contact_factory, user_create):
        """
        Тест на удаление контактной информации
        Ожидаемый результат - подтверждение удаления
        """

        contact = contact_factory(user=user_create, _quantity=1)
        data = {'items': contact[0].id}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = client.delete(self.url, content, content_type=self.content_type)
        assert response.status_code == 200
        assert response.json()['Status'] == True
        assert response.json()['Удалено объектов'] == 1

    def test_del_contact_no_auth(self, client, contact_factory, user_create):
        """
        Тест на удаление контактной информации без аутентификации
        Ожидаемый результат - ошибка
        """

        contact = contact_factory(user=user_create, _quantity=1)
        data = {'items': contact[0].id}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = client.delete(self.url, content, content_type=self.content_type)
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Error'] == 'Log in required'

    def test_del_contact_no_content(self, client, seller_token, contact_factory, user_create):
        """
        Тест на удаление контактной информации без ее указания
        Ожидаемый результат - ошибка
        """
        data = {}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = client.delete(self.url, content, content_type=self.content_type)
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Error'] == 'Не указаны все необходимые аргументы'

    def test_put_contact(self, client, seller_token, contact_factory, user_create):
        """
        Тест на изменение номера телефона
        Ожидаемый результат - подтверждение изменения номера телефона
        """

        contact = contact_factory(user=user_create, phone=89228888888, _quantity=1)
        data = {'id': contact[0].id, 'phone': '79999999999'}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = client.put(self.url, content, content_type=self.content_type)
        assert response.status_code == 201
        new_contact = Contact.objects.get(user=user_create.id)
        assert new_contact.phone == data['phone']

    def test_put_contact_no_auth(self, client, contact_factory, user_create):
        """
        Тест на изменение номера телефона без аутентификации
        Ожидаемый результат - ошибка
        """

        contact = contact_factory(user=user_create, phone=89228888888, _quantity=1)
        data = {'id': contact[0].id, 'phone': '79999999999'}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = client.put(self.url, content, content_type=self.content_type)
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Error'] == 'Log in required'

    def test_put_contact_less_arg(self, client, seller_token, contact_factory, user_create):
        """
        Тест на изменение номера телефона без указания id контакта
        Ожидаемый результат - ошибка
        """

        data = {'phone': '79999999999'}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = client.put(self.url, content, content_type=self.content_type)
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Error'] == 'Не указаны все необходимые аргументы'

    def test_put_contact_wrong_arg(self, client, seller_token, contact_factory, user_create):
        """
        Тест на изменение контактов пользователя с указанием некорректного номера телефона
        Ожидаемый результат - ошибка
        """

        contact = contact_factory(user=user_create, phone=9, _quantity=1)
        data = {'id': contact[0].id, 'phone': '9'}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = client.put(self.url, content, content_type=self.content_type)
        assert response.status_code == 400
        assert response.json()['Errors']['Error'][0] == "Некорректный формат номера"