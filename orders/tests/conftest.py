import pytest
from model_bakery import baker
from backend.models import *
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from orders.settings import DATABASES
from orders.celery import app



@pytest.fixture
def client():
    return APIClient()


@pytest.fixture(scope='session')
def django_db_setup():
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgres',
        'HOST': 'localhost',
        'NAME': 'postgres',
}


@pytest.fixture(scope='module')
def celery_app(request):
    app.conf.update(CELERY_ALWAYS_EAGER=True,
                    CELERY_BROKER_URL='memory://',
                    CELERY_RESULT_BACKEND='memory://')
    return app


@pytest.fixture
def celery_worker_parameters():
    return {
        'perform_ping_check': False,
    }


@pytest.fixture
def user_factory():
    def factory(*args, **kwargs):
        return baker.make(User, *args, **kwargs)
    return factory


@pytest.fixture
def contact_factory():
    def factory(*args, **kwargs):
        return baker.make(Contact, *args, **kwargs)
    return factory


@pytest.fixture
def user_info():
    return {"first_name": "seller", "last_name": "seller", "email": "seller@example.com", "password": "1q2w3e4r5!@",
            "type": "seller", "username": 'seller'}


@pytest.fixture
def user_create(user_info):
    user = User.objects.create_user(email=user_info['email'], first_name=user_info['first_name'],
                                    username=user_info['username'], last_name=user_info['last_name'], is_active=True,
                                    type=user_info['type'])
    user.set_password(user_info['password'])
    user.save()
    return user


@pytest.fixture
def seller_token(client, user_create):
    token = Token.objects.create(user=user_create)
    return client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')


@pytest.fixture
def users_contact_data():
    data = {
        "country": "Russia", "region": "Moscow", "zip": 628000, "city": "Moscow", "street": "Lenin", "house": "21",
        "phone": "+79000000000"
    }
    return data


@pytest.fixture
def categories_factory():
    def factory(*args, **kwargs):
        return baker.make(Category, *args, **kwargs)
    return factory


@pytest.fixture
def product_factory():
    def factory(*args, **kwargs):
        return baker.make(Product, *args, **kwargs)
    return factory


@pytest.fixture
def parameter_factory():
    def factory(*args, **kwargs):
        return baker.make(Parameter, *args, **kwargs)
    return factory


@pytest.fixture
def product_inf_factory():
    def factory(*args, **kwargs):
        return baker.make(ProductInf, *args, **kwargs)
    return factory


@pytest.fixture
def shop_factory():
    def factory(*args, **kwargs):
        return baker.make(Shop, *args, **kwargs)
    return factory


@pytest.fixture
def shop_product_factory():
    def factory(*args, **kwargs):
        return baker.make(ShopProduct, *args, **kwargs)
    return factory


@pytest.fixture
def products_create(categories_factory, product_factory, parameter_factory, product_inf_factory):
    category = categories_factory(_quantity=1)
    parameter = parameter_factory(_quantity=5)
    product = product_factory(category=category[0], _quantity=10)
    for pr in product:
        for pa in parameter:
            product_inf = product_inf_factory(parameter=pa, product=pr)
    asdasd = ProductInf.objects.all()
    return product


@pytest.fixture
def shops_create(products_create, user_factory, shop_factory, shop_product_factory):
    seller = user_factory(_quantity=2, type='seller', is_active=True)
    buyer = user_factory(_quantity=1, type='buyer', is_active=True)
    for s in seller:
        shop = shop_factory(seller=s)
        if len(products_create) > 5:
            shop_product = shop_product_factory(product=products_create.pop(0), shop=shop)
        else:
            shop_product = shop_product_factory(product=products_create.pop(0), shop=shop)


