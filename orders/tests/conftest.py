import pytest
from model_bakery import baker
from backend.models import *
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


@pytest.fixture
def client():
    """
    Фикстура для создания APIclient выполняющиюего тестовые запросы
    """
    return APIClient()


@pytest.fixture
def user_factory():
    """
    Фикстура возвращающая фабрику для создания пользователей
    """
    def factory(*args, **kwargs):
        return baker.make(User, *args, **kwargs)
    return factory


@pytest.fixture
def contact_factory():
    """
    Фикстура возвращающая фабрику для создания контактной информации пользователей
    """
    def factory(*args, **kwargs):
        return baker.make(Contact, *args, **kwargs)
    return factory


@pytest.fixture
def user_info():
    """
    Фикстура возвращающая список аргументов необходимых для регистрации пользователя
    """
    return {"first_name": "seller", "last_name": "seller", "email": "seller@example.com", "password": "1q2w3e4r5!@",
            "type": "seller", "username": 'seller'}


@pytest.fixture
def user_create(user_info):
    """
    Фикстура для пользователя и записи пароля в хешированном виде. Используется в тестах с требованием к аутентификации
    """
    user = User.objects.create_user(email=user_info['email'], first_name=user_info['first_name'],
                                    username=user_info['username'], last_name=user_info['last_name'], is_active=True,
                                    type=user_info['type'])
    user.set_password(user_info['password'])
    user.save()
    return user


@pytest.fixture
def seller_token(client, user_create):
    """
    Фикстура для создания токена аутентификации пользователя-продавка. Возвращает APIclient с http заголовком
    содержащий токен
    """
    token = Token.objects.create(user=user_create)
    return client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')


@pytest.fixture
def buyer_token(client, user_info, users_contact_data):
    """
    Фикстура для создания пользователя-покупателя, его контактной информации и токена аутентификации.
    Возвращает APIclient с http заголовком содержащий токен
    """
    user = User.objects.create_user(email='buyer@example.com', first_name=user_info['first_name'],
                                    username=user_info['username'], last_name=user_info['last_name'], is_active=True,
                                    type='buyer')
    user.set_password(user_info['password'])
    user.save()
    token = Token.objects.create(user=user)
    contact = Contact.objects.create(user=user, country=users_contact_data['country'],
                                     region=users_contact_data['region'], zip=users_contact_data['zip'],
                                     city=users_contact_data['city'], street=users_contact_data['street'],
                                     house=users_contact_data['house'], phone=users_contact_data['phone'])
    return client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')


@pytest.fixture
def users_contact_data():
    """
    Фикстура возвращающая контактную информацию
    """
    data = {
        "country": "Russia", "region": "Moscow", "zip": 628000, "city": "Moscow", "street": "Lenin", "house": "21",
        "phone": "+79000000000"
    }
    return data


@pytest.fixture
def categories_factory():
    """
    Фикстура возвращающая фабрику для создания категорий товаров
    """
    def factory(*args, **kwargs):
        return baker.make(Category, *args, **kwargs)
    return factory


@pytest.fixture
def product_factory():
    """
    Фикстура возвращающая фабрику для создания товаров
    """
    def factory(*args, **kwargs):
        return baker.make(Product, *args, **kwargs)
    return factory


@pytest.fixture
def parameter_factory():
    """
    Фикстура возвращающая фабрику для создания параметров товаров
    """
    def factory(*args, **kwargs):
        return baker.make(Parameter, *args, **kwargs)
    return factory


@pytest.fixture
def product_inf_factory():
    """
    Фикстура возвращающая фабрику для создания информации о товаре
    """
    def factory(*args, **kwargs):
        return baker.make(ProductInf, *args, **kwargs)
    return factory


@pytest.fixture
def shop_factory():
    """
    Фикстура возвращающая фабрику для создания магазинов
    """
    def factory(*args, **kwargs):
        return baker.make(Shop, *args, **kwargs)
    return factory


@pytest.fixture
def shop_product_factory():
    """
    Фикстура возвращающая фабрику для заполнения товаров и информации о нем в конкретном магазине
    """
    def factory(*args, **kwargs):
        return baker.make(ShopProduct, *args, **kwargs)
    return factory


@pytest.fixture
def products_create(categories_factory, product_factory, parameter_factory, product_inf_factory):
    """
    Фикстура для создания товаров с ипользованием фабрики категорий, парамметров и товаров
    Возвращает список товаров
    """
    category = categories_factory(_quantity=1)
    parameter = parameter_factory(_quantity=5)
    product = product_factory(category=category[0], _quantity=10)
    for pr in product:
        for pa in parameter:
            product_inf = product_inf_factory(parameter=pa, product=pr)
    return product


@pytest.fixture
def shops_create(products_create, user_factory, shop_factory, shop_product_factory, client,):
    """
    Фикстура для создания магазинов и заполнения их товарами
    Возвращает id товара необходимого для тестов
    """
    seller = user_factory(_quantity=2, type='seller', is_active=True)
    for s in seller:
        shop = shop_factory(seller=s)
        if len(products_create) > 5:
            shop_product = shop_product_factory(product=products_create.pop(0), shop=shop, price=100000)
        else:
            shop_product = shop_product_factory(product=products_create.pop(0), shop=shop, price=100000)
    return shop_product.id


@pytest.fixture
def basket_create(shops_create, buyer_token):
    """
    Фикстура для создания корзины с товарами
    Возвращает список аргументов - id товара, id заказанного товара, id заказа, id пользователя
    """
    buyer = User.objects.filter(type='buyer').first()
    order = Order.objects.create(user=buyer, status='basket')
    product_info = ShopProduct.objects.filter(id=shops_create).first()
    ordered_items = OrderItem.objects.create(order=order, product_info=product_info, quantity=4)
    return [product_info.id, ordered_items.id, order.id, buyer.id]


@pytest.fixture
def order_create(basket_create, user_info, client):
    """
    Фикстура для создания заказа
    Возвращает список аргументов - API client с токеном авторизации продавца, id заказа, токен авторизации покупателя
    """
    seller = User.objects.filter(type='seller').first()
    seller.set_password(user_info['password'])
    seller.save()
    token = Token.objects.create(user=seller)
    buyer = User.objects.filter(type='buyer').first()
    order = Order.objects.filter(user=buyer).update(status='new')
    buyer_token = Token.objects.filter(user=buyer).first()
    return client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}'), basket_create[2], buyer_token.key
