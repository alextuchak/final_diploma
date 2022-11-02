from rest_framework import serializers
from backend.models import Shop, Contact, User, Category, Product, ShopProduct, Parameter, ProductInf, OrderItem, Order
from rest_framework.exceptions import ValidationError
import re


class ContactSerializer(serializers.ModelSerializer):
    """
        Класс для работы с контактной информацией
    """
    class Meta:
        model = Contact
        fields = ('id', 'country', 'region', 'zip', 'city', 'street', 'house', 'building', 'apartment', 'phone', 'user')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['phone']:
            if re.search(r"((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}", attrs['phone']) is not None:
                return attrs
            else:
                raise ValidationError({'Status': False, 'Errors': "Некорректный формат номера"})
        if attrs['zip']:
            if len(attrs['zip']) <= 10 & attrs['zip'] is not None:
                return attrs
            else:
                raise ValidationError({'Status': False, 'Errors': "Некорректный формат почтового индекса"})


class UserSerializer(serializers.ModelSerializer):
    """
        Класс для работы с информацией о пользователе
    """
    contacts = ContactSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'contacts', 'password', 'type')
        read_only_fields = ('id',)
        extra_kwargs = {"password": {"write_only": True}}


class AccountDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'password', 'type', "is_staff")
        read_only_fields = ('id',)
        extra_kwargs = {"password": {"write_only": True}}


class CategorySerializer(serializers.ModelSerializer):
    """
        Класс для работы с категориями товаров
    """

    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    """
        Класс для работы с магазинами
    """
    seller = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'seller', 'is_work')
        read_only_fields = ('id',)

    def get_seller(self, obj):
        return {"id": obj.seller.id, "last_name": obj.seller.last_name, "first_name": obj.seller.first_name}


class ParameterSerializers(serializers.ModelSerializer):
    """
        Класс для с парамметрами товаров
    """

    class Meta:
        model = Parameter
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ProductInfSerializer(serializers.ModelSerializer):
    """
        Класс для работы с информацией о товаре
    """
    parameter = ParameterSerializers()

    class Meta:
        model = ProductInf
        fields = ('parameter', 'value')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    """
        Класс для работы с товаром
    """
    category = CategorySerializer()
    product_inf = ProductInfSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'model', 'name', 'category', 'product_inf')
        read_only_fields = ('id',)


class ShopProductSerializer(serializers.ModelSerializer):
    """
        Класс для работы с товаром в магазине
    """
    shop = ShopSerializer()
    product = ProductSerializer()

    class Meta:
        model = ShopProduct
        fields = ('id', 'shop', 'product', 'ext_id', 'quantity', 'price', 'price_rrc')
        read_only_fields = ('id',)


class PriceSerializer(serializers.ModelSerializer):
    """
        Класс для работы с ценой товара в конкретном магазине
    """

    class Meta:
        model = ShopProduct
        fields = ('id', 'price')
        read_only_fields = ['price', ]


class OrderItemSerializer(serializers.ModelSerializer):
    """
        Класс для работы с заказанным товаром
    """
    product_info = PriceSerializer

    class Meta:
        model = OrderItem
        fields = ('order', 'product_info', 'quantity')

    def validate(self, attrs):
        if attrs['quantity'] < 1:
            raise ValidationError("Нельзя заказать менее 1 ед!")
        return attrs

    def create(self, validated_data):
        order = super().create(validated_data)
        order.save()
        return order


class BasketViewSerializer(serializers.ModelSerializer):
    """
        Класс для работы товаром в корзине
    """
    product_info = ShopProductSerializer(many=False)

    class Meta:
        model = OrderItem
        fields = ('product_info', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    """
        Класс для работы с заказами
    """
    ordered_items = BasketViewSerializer(many=True, required=False)
    total_sum = serializers.IntegerField(required=False)

    class Meta:
        model = Order
        fields = ('id', 'user', 'dt', 'status', 'ordered_items', 'total_sum')
