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
    Класс регистрации аккаунта. Доступен HTTP method post. За сериализацию данных отвечает класс UserSerializer.
    """

    def post(self, request, *args, **kwargs):
        """
        HTTP method post. В теле json-запроса должны присутствовать поля first_name, last_name, email, password, type.
        Пароль проверяется на сложность методом validate_password. За валидацию всех данных reauest.data отвечает
        UserSerializer. При успешной валидации создается объект класса User, а на указанную почту отправляется email
        с помощью celery task new_user_registered_task
        """
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
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
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
    Класс для подтверждения и активации аккаунта. Доступен http method post.
    """

    def post(self, request, *args, **kwargs):
        """
        HTTP method post. В теле json-запроса должны присутствовать поля email, token. Токен направляется пользователю
        на email после регистрации. При соответствии пары email, token поле is_active в модели User устанавливается в
        значение True, a токен удаляется
        """
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
    Класс для просмотра информации об аккаунте и изменения данных пользователя. Доступен http method get, post. За
    аутентификацию отвечает класс TokenAuthentication
    """

    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        """
        HTTP method get. Метод для получения информации об аккаунте. После проверки методом is_authenticated
        возвращается экземлпяр класса User, за сериализацию данных отвечает класс AccountDetailSerializer
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        serializer = AccountDetailSerializer(request.user)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        HTTP method get. Метод для изменения информации об аккаунте. После проверки методом is_authenticated проверяется
        наличие ключа 'password' в request.data. При обнаружении ключа пароль вроверяется методом validate_password на
        сложность и затем записывается в модель User. За валидацию и изменение других полей модели User овечает класс
        UserSerialier
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if 'password' in request.data:
            errors = {}
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}}, status=400)
            else:
                request.user.set_password(request.data['password'])
                request.user.save()
        else:
            return JsonResponse({'Status': False, 'Error': 'Не указаны все необходимые аргументы'}, status=403)
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True}, status=201)
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


class LoginAccount(APIView):
    """
    Класс для авторизации пользователя. Доступен http method post
    """

    def post(self, request, *args, **kwargs):
        """
        HTTP method post. Метод для авторизации пользователя. В request.data проверяется наличие ключей 'email' и
        'password'. Авторизация просходит методом authentificate который возвращает объект класса User при совпадении
        полей email и password. Если поле is_active=True то для объекта класса создается TokenAuthentication
        """
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
    Класс для обновления прайса магазина с помощью .yaml файла отправленного через http запрос. Доступен http method
    post. За аутентификацию отвечает класс TokenAuthentication
    """
    authentication_classes = (TokenAuthentication,)

    def post(self, request):
        """
        HTTP method post. Метод для загрузки прайса товаров из .yaml файла. После проверки методом is_authenticated
        проверяется тип пользователя. Файл из http запроса загружается в file_form модели ShopFile. После проверки
        валидности формы вызывается celery task handle_uploaded_file_task отвечающий за обновление прайса товаров
        """
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
    Класс для получения списка категорий товаров. Доступен http method get. За сериализацию данных отвечает класс
    CategorySerializer. Фильтрация доступна по полю name
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', ]
    http_method_names = ['get', ]


class ShopViewSet(ModelViewSet):
    """
    Класс для получения списка магазинов. Доступен http method get. За сериализацию данных отвечает класс
    ShopSerializer. Фильтрация доступна по полю name, is_work
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'is_work']
    http_method_names = ['get', ]


class ProductViewSet(ModelViewSet):
    """
    Класс для получения списка товаров. Доступен http method get. За сериализацию данных отвечает класс
    ProductSerializer. Фильтрация доступна по полю name, model. Поиск доступен по полю name, model
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter]
    filterset_fields = ['name', 'model']
    search_fields = ['name', 'model']
    http_method_names = ['get', ]


class ShopProductViewSet(ModelViewSet):
    """
    Класс для получения списка товаров в конкретном магазине. Доступен http method get. За сериализацию данных отвечает
    класс ShopProductSerializer. Поиск доступен по полям product__model, product__name (Поля model и name модели Product)
    """
    queryset = ShopProduct.objects.all()
    serializer_class = ShopProductSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product__model', 'product__name']
    http_method_names = ['get', ]


class ProductInfViewSet(ModelViewSet):
    """
    Класс для получения списка информации о товаре. Доступен http method get. За сериализацию данных отвечает класс
    ProduceInfSerializer. Поиск доступен по полям product_id__model, product_id__name (Поля model и name модели Product)
    """
    queryset = ProductInf.objects.all()
    serializer_class = ProductInfSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['product_id__model', 'product_id__name']
    http_method_names = ['get', ]


class UserContact(APIView):
    """
    Класс для работы с контактной информацией пользователя. Доступен http method get, post, put, delete. За
    аутентификацию отвечает класс TokenAuthentication
    """
    authentication_classes = (TokenAuthentication,)

    def get(self, request, *args, **kwargs):
        """
        HTTP method get. Метод для получения контактной информации о пользователе. После проверки методом
        is_authenticated возвращается экземлпяр класса Contact относящийся к пользователю выполневшему запрос. За
        сериализацию данных отвечает класс ContactSerializer
        """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        HTTP method post. Метод для создания контактной информации о пользователе. После проверки методом
        is_authenticated проверяется наличие ключей 'country', 'region', 'zip', 'city', 'street', 'house', 'phone' в
        request.data. После валидации данных методом is_valid данные сохраняются в БД. За сериализацию данных отвечает
        класс ContactSerializer
        """
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
        """
        HTTP method delete. Метод для удаления контактной информации о пользователе. После проверки методом
        is_authenticated проверяется наличие ключа 'items' в request.data. При нахождении записи в БД с запрашиваемым id
        и принадлежащей пользователю выполневшему запрос, запись удаляется. За сериализацию данных отвечает класс
        ContactSerializer
        """
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
        """
        HTTP method put. Метод для изменения контактной информации о пользователе. После проверки методом
        is_authenticated проверяется наличие ключа 'id' в request.data. При нахождении записи в БД с запрашиваемым id
        и принадлежащей пользователю выполневшему запрос, запись обновляется. За сериализацию данных отвечает класс
        ContactSerializer
        """
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
    Класс для работы с корзиной товаров пользователя. Доступен http method get, post, put, delete. За
    аутентификацию отвечает класс TokenAuthentication
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated]

    #
    def get_queryset(self):
        """
        HTTP method get. Метод для получения информации о товаре в корзине пользователя. После проверки методом
        is_authenticated возвращается экземлпяр класса Order с статусом 'basket' относящийся к пользователю выполневшему
        запрос. За сериализацию данных отвечает класс OrderSerializer.
        """
        queryset = Order.objects.filter(user_id=self.request.user.id, status='basket'). \
            prefetch_related('ordered_items').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        return queryset

    #
    def create(self, request, *args, **kwargs):
        """
        HTTP method post. Метод для создания корзины товаров пользователя. После проверки методом
        is_authenticated создается объект класса Order. Товар и его количество сохраняется в объектах класса OrderItem.
        За сериализацию данных отвечает класс OrderItemSerializer
        """
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
        """
        HTTP method delete. Метод для удаления контактной информации о пользователе. После проверки методом
        is_authenticated проверяется наличие ключа 'items' в request.data. При нахождении записи в БД принадлежащей
        пользователю выполневшему запрос c запрашиваемым id корзины и статусом 'basket', запись удаляется. За
        сериализацию данных отвечает класс OrderItemSerializer
        """
        try:
            items_to_del = str(self.request.data['items']).split(',')
        except KeyError:
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
        """
        HTTP method put. Метод для изменения cсодержимого корзины пользователя. После проверки методом
        is_authenticated происходит валидация данных методом is_valid. При нахождении записи в БД с запрашиваемым
        товаром и принадлежащей пользователю выполневшему запрос и статусом 'basket', обновляется количество товара. За
        сериализацию данных отвечает класс OrderItemSerializer
        """
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
    Класс для работы с заказами пользователя. Доступен http method get, post. За аутентификацию отвечает класс
    TokenAuthentication
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        HTTP method get. Метод для получения информации о заказах пользователя. После проверки методом
        is_authenticated возвращается экземлпяр класса Order с любым статусом, но не 'basket' относящийся к пользователю
        выполневшему запрос. За сериализацию данных отвечает класс OrderSerializer.
        """
        queryset = Order.objects.filter(user_id=self.request.user.id).exclude(status='basket').prefetch_related(
            'ordered_items').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        return queryset

    def create(self, request, *args, **kwargs):
        """
        HTTP method post. Метод для создания корзины товаров пользователя. После проверки методом
        is_authenticated статус объекта класса Order, относящего к пользователю выполневшему запрос, c id указанным в
        запросе обновляется на 'new'. Далее при наличии контактной информации пользователя вызывается celery task
        new_order_task и new_order_for_seller_task для оповещения продавца и покупателя о создании нового заказа.
        """
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
    Класс для продавцов для работы с заказами пользователей. Доступен http method get, put. За аутентификацию отвечает
    класс TokenAuthentication
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        HTTP method get. Метод для получения информации о заказах пользователя. После проверки методом
        is_authenticated возвращается все экземлпяры класса Order с любым статусом, но не 'basket' относящиеся к
        продавцу выполневшему запрос. За сериализацию данных отвечает класс OrderSerializer.
        """
        if self.request.user.type != 'seller':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        queryset = Order.objects.exclude(status='basket').prefetch_related(
            'ordered_items').filter(ordered_items__product_info__shop__seller__id=self.request.user.id).annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()
        return queryset

    @action(methods=['put'], detail=False)
    def put(self, request, *args, **kwargs):
        """
        HTTP method put. Метод для изменения статуса заказа продавцом. После проверки методом
        is_authenticated происходит проверка типа пользователя. При нахождении записи в БД с запрашиваемым
        id обновляется статус заказа. После обновления статуса заказа вызывается celery task order_status_change_task
        Для оповещения продавца и покупателя об изменении статуса заказа.
        За сериализацию данных отвечает класс OrderItemSerializer
        """
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

