from rest_framework import serializers
from backend.models import Shop, Contact, User, Category, Product, ShopProduct, Parameter, ProductInf, OrderItem, Order
from rest_framework.exceptions import ValidationError
import re


class ContactSerializer(serializers.ModelSerializer):
    """
    Класс для сериализации контактной информацией. Обслуживаемая модель - Contact. Обслуживаемые поля - id, country,
    region, zip, city, street, house, building, apartment, phone, user.
    """
    class Meta:
        model = Contact
        fields = ('id', 'country', 'region', 'zip', 'city', 'street', 'house', 'building', 'apartment', 'phone', 'user')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }

    def validate(self, attrs):
        """
        Метод для валидации поля phone. При успешной валидации возвращает весь набор attrs. При несоответствии номера
        телефона возвращает ошибку типа ValidationError
        """
        if attrs['phone']:
            if re.search(r"((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}", attrs['phone']) is not None:
                return attrs
            else:
                raise ValidationError({'Status': False, 'Error': "Некорректный формат номера"}, code=400)


class UserSerializer(serializers.ModelSerializer):
    """
    Класс для сериализации данных пользователя и его контактных данных. Обслуживаемая модель - User. Обслуживаемые поля
    - id, first_name, last_name, email, company, position, contacts, password, type. За  сериализацию данных поля
    contacts отвечает класс ContactSerializer
    """
    contacts = ContactSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'contacts', 'password', 'type')
        read_only_fields = ('id',)
        extra_kwargs = {"password": {"write_only": True}}


class AccountDetailSerializer(serializers.ModelSerializer):
    """
    Класс для сериализации данных пользователя. Обслуживаемая модель - User. Обслуживаемые поля - id, first_name,
    last_name, email, company, position, password, type, is_staff.
    """
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'password', 'type', "is_staff")
        read_only_fields = ('id',)
        extra_kwargs = {"password": {"write_only": True}}


class CategorySerializer(serializers.ModelSerializer):
    """
    Класс для сериализации данных о категориях товаров. Обслуживаемая модель - Category. Обслуживаемые поля - id, name
    """

    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    """
    Класс для сериализации данных о магазинах. Обслуживаемая модель - Shop. Обслуживаемые поля - id, name, url, seller,
    is_work. За сериализацию данных поля seller отвечает метод get_seller возвращающий поля id, last_name, first_name
    объекта User
    """
    seller = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'seller', 'is_work')
        read_only_fields = ('id',)

    def get_seller(self, obj):
        """
        Метод для получения конкретных полей объекта User. Возвращает поля id, last_name, first_name
        """
        return {"id": obj.seller.id, "last_name": obj.seller.last_name, "first_name": obj.seller.first_name}


class ParameterSerializers(serializers.ModelSerializer):
    """
    Класс для сериализации данных о парамметрах товаров. Обслуживаемая модель - Parameter. Обслуживаемые поля - id, name
    """

    class Meta:
        model = Parameter
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ProductInfSerializer(serializers.ModelSerializer):
    """
    Класс для сериализации данных параметров контректного товара. Обслуживаемая модель - ProductInf. Обслуживаемые поля
    - parameter, value. За сериализацию данных поля parameter отвечает класс ParameterSerializer
    """
    parameter = ParameterSerializers()

    class Meta:
        model = ProductInf
        fields = ('parameter', 'value')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    """
    Класс для сериализации данных о товарах. Обслуживаемая модель - Product. Обслуживаемые поля - id, model, name,
    category, product_inf. За сериализацию данных поля category отвечает класс CategorySerializer, за сериализацию
    даных поля product_inf отвечает класс ProductInfSerializer
    """
    category = CategorySerializer()
    product_inf = ProductInfSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'model', 'name', 'category', 'product_inf')
        read_only_fields = ('id',)


class ShopProductSerializer(serializers.ModelSerializer):
    """
    Класс для сериализации данных о товарах в конкретном магазине. Обслуживаемая модель - ShopProduct. Обслуживаемые
    поля - id, shop, product, ext_id, quantity, price, price_rrc. За сериализацию данных поля shop отвечает класс
    ShopSerializer, за сериализацию даных поля product отвечает класс ProductSerializer
    """
    shop = ShopSerializer()
    product = ProductSerializer()

    class Meta:
        model = ShopProduct
        fields = ('id', 'shop', 'product', 'ext_id', 'quantity', 'price', 'price_rrc')
        read_only_fields = ('id',)


class PriceSerializer(serializers.ModelSerializer):
    """
    Класс для сериализации данных о цене товара. Обслуживаемая модель - ShopProduct. Обслуживаемые поля - id, price
    """

    class Meta:
        model = ShopProduct
        fields = ('id', 'price')
        read_only_fields = ['price', ]


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Класс для cериализации данных о товарах в заказе. Обслуживаемая модель - OrderItem. Обслуживаемые поля - order,
    product_info, quantity. За сериализацию данных поля product_info отвечает класс PriceSerializer
    """
    product_info = PriceSerializer

    class Meta:
        model = OrderItem
        fields = ('order', 'product_info', 'quantity')

    def validate(self, attrs):
        """
        Метод для валидации количества заказываемых товаров. При успешной валидации возвращает attrs
        """
        if attrs['quantity'] < 1:
            raise ValidationError("Нельзя заказать менее 1 ед!")
        return attrs

    def create(self, validated_data):
        """
        Метод для создания нового заказа на основе validated_data
        """
        order = super().create(validated_data)
        order.save()
        return order


class BasketViewSerializer(serializers.ModelSerializer):
    """
    Класс для cериализации данных о товарах в корзине. Обслуживаемая модель - OrderItem. Обслуживаемые поля -
    product_info, quantity. За сериализацию данных поля product_info отвечает класс ShopProductSerializer
    """
    product_info = ShopProductSerializer(many=False)

    class Meta:
        model = OrderItem
        fields = ('product_info', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    """
    Класс для cериализации данных о заказах. Обслуживаемая модель - Order. Обслуживаемые поля - id, user, status,
    ordered_items, total_sum. За сериализацию данных поля ordered_items отвечает класс BasketViewSerializer
    """
    ordered_items = BasketViewSerializer(many=True, required=False)
    total_sum = serializers.IntegerField(required=False)

    class Meta:
        model = Order
        fields = ('id', 'user', 'dt', 'status', 'ordered_items', 'total_sum')
