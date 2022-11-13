import pytest
from rest_framework.authtoken.models import Token


@pytest.mark.django_db
class TestULoginAccount:
    """
    Класс для тестирования LoginAccount
    """
    url = 'http://127.0.0.1:8000/user/login'

    def test_user_login(self, client, user_create, user_info):
        """
        Тест на авторизацию
        Ожидаемый результат - авторизация и получение токена
        """
        response = client.post(self.url, data={'email': user_create.email, 'password': user_info['password']})
        assert response.status_code == 201
        token = Token.objects.get(user=user_create.id).key
        assert response.json()['Token'] == token

    def test_user_login_wrong_email(self, client, user_create, user_info):
        """
        Тест на авторизацию с указанием неверного email
        Ожидаемый результат - ошибка
        """
        response = client.post(self.url, data={'email': 'email@email.com', 'password': user_info['password']})
        assert response.status_code == 401
        assert response.json()['Error'] == 'Не удалось авторизовать'

    def test_user_login_less_arg(self, client, user_create, user_info):
        """
        Тест на авторизацию без указания пароля
        Ожидаемый результат - ошибка
        """
        response = client.post(self.url, data={'password': user_info['password']})
        assert response.status_code == 403
        assert response.json()['Error'] == 'Не указаны все необходимые аргументы'