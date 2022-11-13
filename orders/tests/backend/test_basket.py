import pytest
from backend.models import *
from django.test.client import encode_multipart


@pytest.mark.django_db
class TestBasketViewSet:
    """
    Класс для тестирования BasketViewSet
    """
    url = 'http://127.0.0.1:8000/basket/'
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'

    def test_basket_post(self, client, buyer_token, shops_create):
        """
        Тест на добавление товвара в корзину
        Ожидаемый результат - подтверждение добавления товара
        """

        data = [{"product_info": shops_create, "quantity": 4}]
        response = client.post(self.url, data=data)
        assert response.status_code == 201

    def test_basket_post_no_auth(self, client, shops_create):
        """
        Тест на на добавление товаров в корзину без аутентификации
        Ожидаемый результат - ошибка
        """

        data = [{"product_info": shops_create, "quantity": 4}]
        response = client.post(self.url, data=data)
        assert response.status_code == 401
        assert response.json()['detail'] == 'Authentication credentials were not provided.'

    def test_basket_post_wrong_arg(self, client, buyer_token, shops_create):
        """
        Тест на добавление несуществующего товара в корзину
        Ожидаемый результат - ошибка
        """

        data = [{"product_info": 27, "quantity": 4}]
        response = client.post(self.url, data=data)
        assert response.status_code == 400
        assert response.json()['Возникла ошибка!']['product_info'][0] == 'Invalid pk "27" - object does not exist.'

    def test_basket_post_no_data(self, client, buyer_token, shops_create):
        """
        Тест на добавление товаров в корзину без их указания
        Ожидаемый результат - ошибка
        """

        response = client.post(self.url, )
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Возникла ошибка!'] == 'Указаны не все аргументы'

    def test_basket_get(self, client, buyer_token, basket_create):
        """
        Тест на получение списка товаров к корзине
        Ожидаемый результат - список товаров
        """

        response = client.get(self.url)
        assert response.status_code == 200
        assert response.json()[0]['total_sum'] == 400000

    def test_basket_put(self, client, buyer_token, basket_create):
        """
        Тест на изменение количества товара в корзине
        Ожидаемый результат - подтверждение изменения количества товара
        """

        data = [{"product_info": basket_create[0], "quantity": 7}]
        response = client.put(self.url, data=data)
        assert response.status_code == 200
        assert response.json()['Status'] == True
        ordered_items = OrderItem.objects.filter(id=basket_create[1]).first()
        assert data[0]['quantity'] == ordered_items.quantity

    def test_basket_put_no_data(self, client, buyer_token, basket_create):
        """
        Тест на изменение количество товара в корзине без его указания
        Ожидаемый результат - ошибка
        """

        response = client.put(self.url, )
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Error'] == 'Не указаны все необходимые аргументы'

    def test_basket_put_wrong_args(self, client, buyer_token, basket_create):
        """
        Тест на изменение количества товара без указания id корзины
        Ожидаемый результат - ошибка
        """

        data = [{"quantity": 7}]
        response = client.put(self.url, data=data)
        assert response.status_code == 403
        assert response.json()['Возникла ошибка!']['product_info'][0] == 'This field is required.'

    def test_basket_delete(self, client, buyer_token, basket_create):
        """
        Тест на удаление позиции из корзины
        Ожидаемый результат - подтверждение удаления товара из корзины
        """

        data = {'items': basket_create[0]}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = client.delete(self.url, content, content_type=self.content_type)
        assert response.status_code == 200
        basket = OrderItem.objects.all()
        assert len(basket) == 0

    def test_basket_delete_wrong_arg(self, client, buyer_token, basket_create):
        """
        Тест на удаление несуществующей позиции из корзины
        Ожидаемый результат - ошибка
        """

        data = {'items': 5555}
        content = encode_multipart('BoUnDaRyStRiNg', data)
        response = client.delete(self.url, content, content_type=self.content_type)
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Error'] == 'Укажите корректные товары для удаления'

    def test_basket_delete_no_arg(self, client, buyer_token, basket_create):
        """
        Тест на удаление позиций из корзины без указания удаляемых позиций
        Ожидаемый результат - ошибка
        """

        response = client.delete(self.url, )
        assert response.status_code == 403
        assert response.json()['Status'] == False
        assert response.json()['Error'] == 'Не указаны все необходимые аргументы'