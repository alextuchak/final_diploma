import pytest
from backend.models import *


@pytest.mark.django_db
class TestAccountDetails:
    """
    Класс для тестирования AccountDetails
    """
    url = 'http://127.0.0.1:8000/user/info'
    data = {'password': '!Q@W#E$R%T^T12'}

    def test_get_user_info(self, client, seller_token):
        """
        Тест на получение информации об аккаунте пользователя
        Ожидаемый результат - список информации об аккаунте
        """

        response = client.get(self.url)
        assert response.status_code == 200
        assert response.json()['email'] == 'seller@example.com'

    def test_get_user_info_no_auth(self, client):
        """
        Тест на получение информации об аккаунте пользователя без аутентификации
        Ожидаемый результат - ошибка
        """

        response = client.get(self.url)
        assert response.status_code == 403
        assert response.json()['Error'] == 'Log in required'

    def test_user_change_password(self, client, seller_token, user_info):
        """
        Тест на изменение пароля пользователя
        Ожидаемый результат - подтверждение изменения пароля
        """

        response = client.post(self.url, data=self.data)
        assert response.status_code == 201
        assert response.json()['Status'] == True
        password = User.objects.get(email=user_info['email']).password
        assert password == '!Q@W#E$R%T^T12'

    def test_user_chg_pass_less_args(self, client, seller_token):
        """
        Тест на изменение пароля пользователя без указания пароля
        Ожидаемыйы результат - ошибка
        """

        response = client.post(self.url)
        assert response.status_code == 403
        assert response.json()['Error'] == 'Не указаны все необходимые аргументы'

    def test_user_chg_pass_no_auth(self, client):
        """
        Тест на изменение пароля пользователя без аутентификации
        Ожидаемый результат - ошибка
        """

        response = client.post(self.url, data=self.data)
        assert response.status_code == 403
        assert response.json()['Error'] == 'Log in required'

    @pytest.mark.django_db
    def test_user_chg_pass_common(self, client, seller_token):
        """
        Тест на изменение пароля пользователя на простой пароль
        Ожидаемый результат - ошибка
        """
        response = client.post(self.url, data={'password': '123'})
        assert response.status_code == 400
        assert response.json()['Errors']['password'][0] == 'This password is too short. ' \
                                                           'It must contain at least 8 characters.'