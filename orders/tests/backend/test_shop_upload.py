import pytest
import os
from mock import patch
from django.test.client import encode_multipart
from orders.settings import BASE_DIR



@pytest.mark.django_db
class TestShopUpload:
    """
    Класс для тестирования ShopUpload
    """
    url = 'http://127.0.0.1:8000/shop/upload'
    content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    data = {'file': ('shop1.yaml', open(os.path.join(BASE_DIR + '/data/shop1.yaml')), 'rb')}

    def test_shop_inf_upload(self,client, seller_token):
        """
        Тест на обновление прайса товаров
        Ожидаемый результат - подтверждение обновления
        """
        with patch('backend.tasks.handle_uploaded_file_task') as mock_task:
            content = encode_multipart('BoUnDaRyStRiNg', self.data)
            response = client.post(self.url, content, content_type=self.content_type)
            assert response.status_code == 201

    def test_shop_inf_upload_no_auth(self, client):
        """
        Тест на обновление прайса товаров без аутентификации
        Ожидаемый результат - ошибка
        """
        with patch('backend.tasks.handle_uploaded_file_task') as mock_task:
            content = encode_multipart('BoUnDaRyStRiNg', self.data)
            response = client.post(self.url, content, content_type=self.content_type)
            assert response.status_code == 403
            assert response.json()['Status'] == False
            assert response.json()['Error'] == 'Log in required'

    def test_shop_inf_upload_buyer(self, client, buyer_token):
        """
        Тест на обновление прайса товаров покупателем
        Ожидаемый результат - ошибка
        """
        with patch('backend.tasks.handle_uploaded_file_task') as mock_task:
            content = encode_multipart('BoUnDaRyStRiNg', self.data)
            response = client.post(self.url, content, content_type=self.content_type)
            assert response.status_code == 403
            assert response.json()['Status'] == False
            assert response.json()['Error'] == 'Только для магазинов'

    def test_shop_inf_upload_wrong_arg(self, client, seller_token):
        """
        Тест на обновление прайса товаров с неверно указанными аргументами
        Ожидаемый результат - ошибка
        """
        with patch('backend.tasks.handle_uploaded_file_task') as mock_task:
            data = {'yaml': ('shop1.yaml', open(os.path.join(BASE_DIR + '/data/shop1.yaml')), 'rb')}
            content = encode_multipart('BoUnDaRyStRiNg', data)
            response = client.post(self.url, content, content_type=self.content_type)
            assert response.status_code == 400
            assert response.json()['Status'] == False