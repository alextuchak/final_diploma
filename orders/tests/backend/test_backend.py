import pytest


@pytest.mark.django_db
def test_get_categeroies(client, categories_factory):
    """
    Тест на получение списка категорий товаров
    Ожидаемый результат - список категорий товаров
    """
    url = 'http://127.0.0.1:8000/categories/'
    categories = categories_factory(_quantity=3)
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.django_db
def test_get_products(client, products_create):
    """
    Тест на получение списка товаров
    Ожидаемый результат - список товаров
    """
    url = 'http://127.0.0.1:8000/products/'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 10


@pytest.mark.django_db
def test_get_products_inf(client, products_create):
    """
    Тест на получение списка информации о продуктах
    Ожидаемый результат - список с информацией о продуктах
    """
    url = 'http://127.0.0.1:8000/product_inf/'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 50


@pytest.mark.django_db
def test_get_shops(client, shops_create):
    """
    Тест на на получение списка магазинов
    Ожидаемый результат - список магазинов
    """
    url = 'http://127.0.0.1:8000/shops/'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.django_db
def test_get_products_in_shop(client, shops_create):
    """
    Тест на получение товаров в магазинах
    Ожидаемый результат - список товаров в магазинах
    """
    url = 'http://127.0.0.1:8000/products_in_shop/'
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 2