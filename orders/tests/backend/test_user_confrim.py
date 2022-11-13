import pytest
from backend.models import *


@pytest.mark.django_db
class TestConfirmAccount:
    """
    Класс для тестирования ConfirmAccount
    """

    url = 'http://127.0.0.1:8000/user/register/confirm'

    def test_user_confirm(self, client, user_create):
        """
        Тест на подтверждение аккаунта
        Ожидаемый результат - подтверждение аккаунта
        """

        token = ConfirmEmailToken.objects.create(user=user_create)
        response = client.post(self.url, data={'email': user_create.email, 'token': token.key})
        assert response.status_code == 201
        assert response.json()['Status'] == True

    def test_user_conf_wrong_email(self, client, user_create):
        """
        Тест на подтверждение аккаунта с указанием неверного email
        Ожидаемый результат - ошибка
        """

        token = ConfirmEmailToken.objects.create(user=user_create)
        response = client.post(self.url, data={'email': 'email@email.com', 'token': token.key})
        assert response.status_code == 403
        assert response.json()['Error'] == 'Неправильно указан токен или email'

    def test_user_conf_less_arg(self, client, user_create):
        """
        Тест на подтверждение аккаунта без указания email
        Ожидаемый результат - ошибка
        """

        token = ConfirmEmailToken.objects.create(user=user_create)
        response = client.post(self.url, data={'token': token.key})
        assert response.status_code == 403
        assert response.json()['Error'] == 'Не указаны все необходимые аргументы'