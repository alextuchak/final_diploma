from rest_framework.authentication import TokenAuthentication

from .forms import UploadFileForm
from django.http import JsonResponse
from rest_framework.views import APIView
from backend.models import Shop, Category, Product, ShopProduct, ProductInf, ConfirmEmailToken, \
    Contact, Order, OrderItem
from orders.settings import DATA_ROOT
import os
from django.contrib.auth.password_validation import validate_password
from backend.serializers import UserSerializer, CategorySerializer, ShopSerializer, ProductSerializer, \
    ShopProductSerializer, ProductInfSerializer, ContactSerializer, OrderSerializer, OrderItemSerializer, \
    AccountDetailSerializer
from backend.tasks import new_user_registered_task, new_order_task, new_order_for_seller_task, \
    order_status_change_task, handle_uploaded_file_task
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.viewsets import ModelViewSet
from rest_framework import filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, F
from django.db import IntegrityError


class RegisterAccount(APIView):
    """
        Класс для регистрации пользователей
    """

    def post(self, request, *args, **kwargs):
        if {'first_name', 'last_name', 'email', 'password', 'type'}.issubset(request.data):
            errors = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}}, status=403)
            else:
                # проверяем данные для уникальности имени пользователя
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    new_user_registered_task.delay(user_id=user.id)
                    return JsonResponse({'Status': True}, status=201)
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors}, status=400)

        return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=400)


class ConfirmAccount(APIView):
    """
        Класс для подтверждения и активации аккаунта
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
                return JsonResponse({'Status': True}, status=201)
            else:
                return JsonResponse({'Status': False, 'Error': 'Неправильно указан токен или email'}, status=403)

        return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)


class AccountDetails(APIView):
    """
        Класс для работы с информацией об аккаунте
    """

    authentication_classes = (TokenAuthentication,)

    # получить данные
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        serializer = AccountDetailSerializer(request.user)
        return Response(serializer.data)

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
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}}, status=400)
            else:
                request.user.set_password(request.data['password'])
                request.user.save()
        else:
            return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)
        # проверяем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True}, status=201)
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
                    return JsonResponse({'Status': True, 'Token': token.key}, status=201)

            return JsonResponse({'Status': False, 'Error': 'Не удалось авторизовать'}, status=401)

        return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)


class ShopUpload(APIView):
    """
        Класс для импорта товорав в магазин
    """
    authentication_classes = (TokenAuthentication,)

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if request.user.type != 'seller':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            file = request.FILES.popitem()
            handle_uploaded_file_task.delay(os.path.join(DATA_ROOT, str(file[1][0])), request.user.id)
            return JsonResponse({'Status': True}, status=201)
        else:
            return JsonResponse({'Status': False}, status=400)


class CategoryViewSet(ModelViewSet):
    """
        Класс для просмотра категорий товаров
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', ]
    http_method_names = ['get', ]


class ShopViewSet(ModelViewSet):
    """
        Класс для просмотра магазинов
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'is_work']
    http_method_names = ['get', ]


class ProductViewSet(ModelViewSet):
    """
        Класс для просмотра товара
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    filterset_fields = ['name', 'model']
    search_fields = ['name', 'model']
    http_method_names = ['get', ]


class ShopProductViewSet(ModelViewSet):
    """
        Класс для просмотра товара в конкретном магазине
    """
    queryset = ShopProduct.objects.all()
    serializer_class = ShopProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product__model', 'product__name']
    http_method_names = ['get', ]


class ProductInfViewSet(ModelViewSet):
    """
        Класс для просмотра информации о товаре
    """
    queryset = ProductInf.objects.all()
    serializer_class = ProductInfSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product_id__model', 'product_id__name']
    http_method_names = ['get', ]


class UserContact(APIView):
    """
        Класс для работы с контактной информацией пользователя
    """
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if {'country', 'region', 'zip', 'city', 'street', 'house', 'phone'}.issubset(request.data):
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True}, status=201)
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors}, status=400)
        return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                if contact:
                    serializer = ContactSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True}, status=201)
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors}, status=400)

        return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)


class BasketViewSet(ModelViewSet):
    """
    Класс для выполнения операций с корзиной товаров
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated]

    #
    def get_queryset(self):
        queryset = Order.objects.filter(user_id=self.request.user.id, status='basket'). \
            prefetch_related('ordered_items').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        return queryset

    #
    def create(self, request, *args, **kwargs):
        if self.request.data:
            try:
                objects_created = 0
                order, _ = Order.objects.get_or_create(user_id=self.request.user.id, status='basket')
                for items in self.request.data:
                    serializer = OrderItemSerializer(data=items)
                    if serializer.is_valid():
                        try:
                            serializer.save(order_id=order.id)
                            objects_created += 1
                        except IntegrityError as err:
                            return JsonResponse(err)
                    else:
                        return JsonResponse({'Status': False, 'Возникла ошибка!': serializer.errors}, status=400)
                return JsonResponse({'Status': True, 'Добавлено объектов': objects_created}, status=201)
            except TypeError as error:
                return JsonResponse({error})
        return JsonResponse({'Status': False, 'Возникла ошибка!': "Указаны не все аргументы"}, status=403)

    #
    @action(methods=['delete'], detail=False)
    def delete(self, request, *args, **kwargs):
        try:
            items_to_del = str(self.request.data['items']).split(',')
        except KeyError :
            return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)
        if items_to_del:
            basket, _ = Order.objects.get_or_create(user_id=self.request.user.id, status='basket')
            query = Q()
            deleted_status = False
            for order_item_id in items_to_del:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, product_info_id=order_item_id)
                    deleted_status = True
            if deleted_status:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                if deleted_count != 0:
                    return JsonResponse({'Status': True, 'Удалено объектов': deleted_count}, status=200)
                else:
                    return JsonResponse({'Status': False, 'Error': 'Укажите корректные товары для удаления'},
                                        status=403)
        return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)

    #
    @action(methods=['put'], detail=False)
    def put(self, request, *args, **kwargs):
        if self.request.data:
            try:
                objects_updated = 0
                basket, _ = Order.objects.get_or_create(user_id=self.request.user.id, status='basket')
                for items in self.request.data:
                    items.update(order_id=basket.id)
                    serializer = OrderItemSerializer(data=items)
                    if serializer.is_valid():
                        if type(items['product_info']) == int and type(items['quantity']) == int:
                            objects_updated += OrderItem.objects.filter(order_id=basket.id,
                                                                        product_info_id=items['product_info']).update(
                                quantity=items['quantity'])
                    else:
                        return JsonResponse({'Status': False, 'Возникла ошибка!': serializer.errors}, status=403)
                return JsonResponse({"Status": True, "Обновлено объектов": objects_updated}, status=200)
            except ValueError:
                return JsonResponse({'Status': False, 'Возникла ошибка!': "Некорректный формат данных"})
        return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)


class OrderViewSet(ModelViewSet):
    """
    Класс для выполнения операций с заказами
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.filter(user_id=self.request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        return queryset

    def create(self, request, *args, **kwargs):
        if {'id'}.issubset(self.request.data):
            if self.request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(id=self.request.data['id']).update(status='new')
                except IntegrityError:
                    return JsonResponse({'Status': False, 'Error': 'Аргументы указаны неверно'})
                else:
                    if is_updated:
                        contacts = Contact.objects.filter(user_id=self.request.user.id).first()
                        if contacts:
                            seller = Order.objects.filter(id=self.request.data['id']).prefetch_related(
                                'ordered_items').all()[0].ordered_items.all()[0]
                            new_order_task.delay(user_id=self.request.user.id,
                                                 order_id=self.request.data['id'])
                            new_order_for_seller_task.delay(user_id=seller.product_info.shop.seller.id,
                                                            order_id=self.request.data['id'],
                                                            buyer_id=self.request.user.id)

                            return JsonResponse({'Status': True}, status=201)
                        else:
                            return JsonResponse({'Status': False, 'Error': 'Не указаны контакты для связи'},
                                                status=403)

        return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)


class SellerOrderViewSet(ModelViewSet):
    """
       Класс для продавцов для выполнения операций с заказами

    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.type != 'seller':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        queryset = Order.objects.exclude(status='basket').prefetch_related(
            'ordered_items').filter(ordered_items__product_info__shop__seller__id=self.request.user.id).annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        return queryset

    @action(methods=['put'], detail=False)
    def put(self, request, *args, **kwargs):
        if request.user.type != 'seller':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        if 'id' and 'status' in self.request.data:
            try:
                order = Order.objects.filter(id=self.request.data['id']).update(status=self.request.
                                                                                    data['status'])
                buyer = Order.objects.filter(id=self.request.data['id']).first()
                order_status_change_task.delay(user_id=self.request.user.id,
                                                   order_id=self.request.data['id'],
                                                   buyer_id=buyer.user_id)
                return JsonResponse({"Status": True, "Статус заказа обновлен": self.request.data['status']}, status=201)
            except IntegrityError:
                return JsonResponse({'Status': False, 'Возникла ошибка!': "Некоректный формат данных"}, status=403)
        else:
            return JsonResponse({'Status': False, 'Возникла ошибка!': "Некоректный формат данных"}, status=403)

