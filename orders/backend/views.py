from django.shortcuts import render
from .forms import UploadFileForm
from django.http import JsonResponse
from rest_framework.views import APIView
from backend.models import Shop, ShopFiles, Category, Product, ShopProduct, Parameter, ProductInf, ConfirmEmailToken
import yaml
from orders.settings import BASE_DIR, DATA_ROOT
import os
from django.contrib.auth.password_validation import validate_password
from backend.serializers import UserSerializer
from backend.signals import new_user_registered, new_order
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate


class RegisterAccount(APIView):
    def post(self, request, *args, **kwargs):
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            errors = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                # проверяем данные для уникальности имени пользователя
                request.data._mutable = True
                request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    new_user_registered.send(sender=self.__class__, user_id=user.id)
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса
    """
    # Регистрация методом POST
    def post(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class AccountDetails(APIView):
    """
    Класс для работы данными пользователя
    """

    # получить данные
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # Редактирование методом POST
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        # проверяем обязательные аргументы

        if 'password' in request.data:
            errors = {}
            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])

        # проверяем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """
    # Авторизация методом POST
    def post(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

class ShopUpload(APIView):
    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            file = request.FILES.popitem()
            self.handle_uploaded_file(os.path.join(DATA_ROOT, str(file[1][0])))
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False})

    def handle_uploaded_file(sefl, shop_file):
        shop = Shop()
        product = Product()
        parameter = Parameter()
        with open(shop_file, 'r', encoding='utf8') as stream:
            try:
                shop_data = yaml.safe_load(stream)
                shop.name = shop_data['shop']
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
                    prod_pk = Product.objects.filter(model=goods['model']).first()
                    shopproduct_object, _ = ShopProduct.objects.get_or_create(ext_id=goods['id'],
                                                                              quantity=goods['quantity'],
                                                                              price=goods['price'],
                                                                              price_rrc=goods['price_rrc'],
                                                                              product=prod_pk, shop=shop)
                    shopproduct_object.save()
                    for parameters, value in goods['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=parameters)
                        parameter_object.save()
                        product_inf_object, _ = ProductInf.objects.get_or_create(value=value, product=prod_pk,
                                                                                 parameter=parameter_object)
                        product_inf_object.save()
            except yaml.YAMLError as exc:
                return JsonResponse({'Status': False, 'Error': str(exc)})
