import pytest
from mock import patch


@pytest.mark.django_db
class TestRegisterAccount:
    """
    Класс для тестирования RegisterAccount
    """
    url = 'http://127.0.0.1:8000/user/register'

    def test_user_registration(self, client, user_info,):
        """
        Тест на регистрацию пользователя
        Ожидаемый результат - подтверждение регистрации
        """
        with patch('backend.tasks.new_user_registered_task') as mock_task:
            response = client.post(self.url, data=user_info)
            assert response.status_code == 201

    def test_user_reg_common_password(self, client, user_info):
        """
        Тест на регистрацию пользователя с простым паролем
        Ожидаемый результат - ошибка
        """
        user_info.update({'password': '123'})
        response = client.post(self.url, data=user_info)
        assert response.status_code == 403
        assert response.json()['Errors']['password'][1] == 'This password is too common.'

    @pytest.mark.django_db
    def test_user_reg_less_arg(self, client, user_info):
        """
        Тест на регистрацию пользователя без указания всех необходимых аргументов
        Ожидаемый результат - ошибка
        """
        user_info.pop('first_name')
        response = client.post(self.url, data=user_info)
        assert response.status_code == 400
        assert response.json()['Error'] == 'Не указаны все необходимые аргументы'