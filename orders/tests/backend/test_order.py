from django.test.client import encode_multipart
import pytest
from backend.models import *
from mock import patch


@pytest.mark.django_db
class TestOrderViewSet:
    """
            Класс для тестирования OrderViewSet
    """
    url = 'http://127.0.0.1:8000/order/customer/'
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

    def test_order_create(self, client, buyer_token, basket_create):
        """
        Тест на созданиеи заказа пользователем
        Ожидаемый результат - подтверждение создания заказа
        """
        with patch('backend.tasks.new_order_task') as mock_task1:
            with patch('backend.tasks.new_order_for_seller_task') as mock_task2:
                data = {'id': basket_create[2]}
                content = encode_multipart('BoUnDaRyStRiNg', data)
                response = client.post(self.url, content, content_type=self.content_type)
                assert response.status_code == 201

    def test_order_create_without_contact(self, client, buyer_token, basket_create):
        """
        Тест на создание заказа пользователем без контактов для обратной связи
        Ожидаемый результат - ошибка
        """
        with patch('backend.tasks.new_order_task') as mock_task1:
            with patch('backend.tasks.new_order_for_seller_task') as mock_task2:
                cotact = Contact.objects.filter(user=basket_create[3]).delete()
                data = {'id': basket_create[2]}
                content = encode_multipart('BoUnDaRyStRiNg', data)
                response = client.post(self.url, content, content_type=self.content_type)
                assert response.status_code == 403
                assert response.json()['Error'] == 'Не указаны контакты для связи'

    def test_order_create_no_data(self, client, buyer_token, basket_create):
        """
        Тест на создание заказа без необходимых данных
        Ожидаемый результат - ошибка
        """
        with patch('backend.tasks.new_order_task') as mock_task1:
            with patch('backend.tasks.new_order_for_seller_task') as mock_task2:
                response = client.post(self.url,)
                assert response.status_code == 403
                assert response.json()['Error'] == 'Не указаны все необходимые аргументы'