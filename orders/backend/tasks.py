from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django_rest_passwordreset.signals import reset_password_token_created
from orders.celery import app
from backend.models import ConfirmEmailToken, User, Shop, Contact, Order, Product, Parameter, Category, ShopProduct, \
    ProductInf
import yaml
from django.http import JsonResponse


@app.task
def password_reset_token_created_task(reset_password_token, **kwargs):
    """
    Отправляем письмо с токеном для сброса пароля
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param kwargs:
    :return:
    """
    # send an e-mail to the user

    msg = EmailMultiAlternatives(
        # title:
        f"Password Reset Token for {reset_password_token.user}",
        # message:
        reset_password_token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [reset_password_token.user.email]
    )
    msg.send()


@app.task
def new_user_registered_task(user_id, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
    # send an e-mail to the user
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        f"Token for confirm registration {token.user.email}",
        # message:
        token.key,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [token.user.email]
    )
    msg.send()


@app.task
def new_order_task(user_id, **kwargs):
    """
    отправяем письмо при формировании нового заказа
    """
    # send an e-mail to the user
    user = User.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # title:
        "Cпасибо за заказ",
        # message:
        f'Номер вашего заказа: {kwargs["order_id"]}\n'
        f'Наш оператор свяжется с Вами в ближайшее время для уточнения деталей заказа.'
        f'Статус заказов вы можете посмотреть в разделе "Заказы"'
        ,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()


@app.task
def new_order_for_seller_task(user_id, **kwargs):
    """
        отправяем письмо продавцу при формировании нового заказа
    """
    # send an e-mail to the user
    user = User.objects.get(id=user_id)
    shop = Shop.objects.get(seller_id=user_id)
    buyer = User.objects.get(id=kwargs["buyer_id"])
    buyer_contacts = Contact.objects.get(user_id=kwargs["buyer_id"])
    msg = EmailMultiAlternatives(
        # title:
        f'Новый заказ {kwargs["order_id"]}',
        # message:
        f'В магазине {shop.name} оформлен новый заказ номер {kwargs["order_id"]}\n'
        f'Свяжитесь с покупателем уточнения деталей заказа.'
        f'Контактная информация: {buyer.first_name} {buyer.last_name}'
        f'Телефон: {buyer_contacts.phone}'
        f'Адресс доставки: Страна {buyer_contacts.country},{buyer_contacts.region} область, почтовый индекс {buyer_contacts.zip}, '
        f'город {buyer_contacts.city}, улица {buyer_contacts.street}, дом {buyer_contacts.house}, строение {buyer_contacts.building},'
        f'квартира {buyer_contacts.apartment}\n'
        f'Статус заказов вы можете посмотреть в разделе "Заказы"'
        ,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email]
    )
    msg.send()


@app.task
def order_status_change_task(user_id, **kwargs):
    """
        отправяем письмо при изменении статуса заказа покупателю и продавцу
    """
    # send an e-mail to the user
    user = User.objects.get(id=user_id)

    buyer = User.objects.get(id=kwargs["buyer_id"])

    order = Order.objects.get(id=kwargs["order_id"])

    msg = EmailMultiAlternatives(
        # title:
        f'Изменения статуса заказа {kwargs["order_id"]}',
        # message:
        f'Статус заказа: {kwargs["order_id"]} изменен на {order.status}\n'
        f'Статус заказов вы можете посмотреть в разделе "Заказы"'
        ,
        # from:
        settings.EMAIL_HOST_USER,
        # to:
        [user.email, buyer.email]
    )
    msg.send()


@app.task
def handle_uploaded_file_task(shop_file, user):
    shop = Shop()
    with open(shop_file, 'r', encoding='utf8') as stream:
        try:
            shop_data = yaml.safe_load(stream)
            shop.name = shop_data['shop']
            seller = User.objects.filter(id=user).first()
            shop.seller = seller
            shop.save()
            for category in shop_data['categories']:
                category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                category_object.shops.add(shop)
                category_object.save()
            for goods in shop_data['goods']:
                category = Category.objects.get(id=goods['category'])
                product_object, _ = Product.objects.get_or_create(name=goods['name'], model=goods['model'],
                                                                  category=category)
                product_object.save()
                prod_pk = Product.objects.filter(name=goods['name']).first()
                shopproduct_object, _ = ShopProduct.objects.get_or_create(ext_id=goods['id'],
                                                                          quantity=goods['quantity'],
                                                                          price=goods['price'],
                                                                          price_rrc=goods['price_rrc'],
                                                                          product=prod_pk, shop=shop)
                shopproduct_object.save()
                for parameters, value in goods['parameters'].items():
                    parameter_object, _ = Parameter.objects.get_or_create(name=parameters)
                    parameter_object.save()
                    param_obj_pk = Parameter.objects.filter(name=parameters).first()
                    product_inf_object, _ = ProductInf.objects.get_or_create(value=value,
                                                                             parameter=param_obj_pk,
                                                                             product=prod_pk)
                    product_inf_object.save()
        except yaml.YAMLError as exc:
            return JsonResponse({'Status': False, 'Error': str(exc)})
