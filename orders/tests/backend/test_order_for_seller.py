import pytest
from mock import patch


@pytest.mark.django_db
class TestSellerOrderViewSet:
    """
    Класс для тестирования SellerOrderViewSet
    """

    url = 'http://127.0.0.1:8000/order/seller/'

    def test_order_get_by_seller(self, client, order_create):
        """
        Тест на просмотр новых заказов продавцом
        Ожидаемый результат - список заказов
        """

        response = client.get(self.url)
        assert response.status_code == 200

    def test_order_put_by_seller(self, client, order_create):
        """
        Тест на изменение статуса заказа продавцом
        Ожидаемый результат - подтверждение изменения статуса заказа
        """

        with patch('backend.tasks.order_status_change_task') as mock_task:
            data = {"id": order_create[1], "status": "confirmed"}
            response = client.put(self.url, data)
            assert response.status_code == 201
            assert response.json()["Статус заказа обновлен"] == data['status']

    def test_order_put_by_seller_wrong_data(self, client, order_create):
        """
        Тест на изменение статуса заказа без указания измененного статуса заказа
        Ожидаемый результат - ошибка
        """

        with patch('backend.tasks.order_status_change_task') as mock_task:
            data = {"id": order_create[1]}
            response = client.put(self.url, data)
            assert response.status_code == 403
            assert response.json()['Возникла ошибка!'] == "Некоректный формат данных"

    def test_order_put_by_buyer(self, client, order_create):
        """
        Тест на изменение статуса заказа покупателем методом put.
        Ожидаемый результат ошибка так как данная функция разрешена только для аккаунтов-продавцов
        """

        with patch('backend.tasks.order_status_change_task') as mock_task:
            data = {"id": order_create[1], "status": "confirmed"}
            client.credentials(HTTP_AUTHORIZATION=f'Token {order_create[2]}')
            response = client.put(self.url, data,)
            assert response.status_code == 403
            assert response.json()['Error'] == 'Только для магазинов'