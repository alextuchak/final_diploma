from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
import django_rest_passwordreset.tokens

USER_TYPE_CHOICES = (
    ('seller', 'Продавец'),
    ('buyer', 'Покупатель'),
)

STATUS_CHOICES = (
    ('basket', 'В корзине'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)


class CustomUser(BaseUserManager):
    """
    Класс для создания базовой модели пользователя. Наследуется от BaseUserManager
    Методы класса - create, create_user, create_super_user
    """
    use_in_migrations = True

    def create(self, email, password, **extra_fields):
        """
        Метод создания пользователя, возвращает объект user.
        """
        if not email:
            raise ValueError('The email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password, **extra_fields):
        """
        Метод для создания покупателя. Поля is_staff is_super устанавливаются по умолчанию в значение False.
        Результат выполнения вызов метода create с заданными аргументами
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self.create(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """
        Метод для создания продавца. Поля is_staff, is_superuser, is_active устанавливаются по умолчанию в значение True.
        Установка значения is_active True необходимо для админки django.
        Результат выполнения вызов метода create с заданными аргументами
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have status is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have status is_superuser=True')
        return self.create(email, password, **extra_fields)


class User(AbstractUser):
    """
    Класс для создания модели пользователя. Наследуется от AbstractUser. Для авторизации по email поле USERNAME_FIELD
    переназначено на email. Поле type можем быть только одним из значений переменной USER_TYPE_CHOICES
    Поля в модели:
    email - EmailField, company - CharField, position - CharField, username - CharField, - is_active  - BooleanField,
    type - CharField
    """
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    object = CustomUser()
    email = models.EmailField(_('email adress'), unique=True)
    company = models.CharField(verbose_name='Компания', max_length=64, blank=True)
    position = models.CharField(verbose_name='Должность', max_length=32, blank=True)
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(_('username'),
                                max_length=128,
                                help_text=_('Required. 128 characters or fewer. Letters, digits and @/./+/-/_ only.'),
                                validators=[username_validator],
                                error_messages={
                                    'unique': _("A user with that username already exists."),
                                })
    is_active = models.BooleanField(_('active'),
                                    default=False,
                                    help_text=_(
                                        'Designates whether this user should be treated as active. '
                                        'Unselect this instead of deleting accounts.'
                                    ))
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=16, default='buyer')

    def __str__(self):
        """
        Переоопределени магического метода для строкового отображения нужных полей экземпляра класса
        """
        return f'{self.first_name} {self.last_name}'

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку пользоватей
        в админке django
        """
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Список пользователей'
        ordering = ('email',)


class Shop(models.Model):
    """
    Класс для создания модели магазина. Поля в модели:
    name - CharField, url - URLField, seller - OneToOneField (User), is_work - BooleanField
    """
    name = models.CharField(max_length=64, verbose_name='Название магазина', unique=True)
    url = models.URLField(blank=True, null=True, verbose_name='Ссылка')
    seller = models.OneToOneField(User, verbose_name='Продавец', blank=True, null=True,
                                  on_delete=models.CASCADE)
    is_work = models.BooleanField(verbose_name='Доступность', default=True)

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку магазинов
        в админке django
        """
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'
        ordering = ('-name',)

    def __str__(self):
        """
        Переоопределени магического метода для строкового отображения нужных полей экземпляра класса
        """
        return self.name


class Category(models.Model):
    """
    Класс для создания модели катеогии товаров. Поля в модели:
    name - CharField, id - PositiveIntegerField, Shops - ManyToManyField (Shop)
    """
    name = models.CharField(max_length=32, verbose_name='Название категории')
    id = models.PositiveIntegerField(verbose_name='ИД категории', primary_key=True)
    shops = models.ManyToManyField(Shop, verbose_name='Магазины', related_name='categories', blank=True)

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку категорий
        в админке django
        """
        verbose_name = 'Категория'
        verbose_name_plural = 'Список категорий'
        ordering = ('-name',)

    def __str__(self):
        """
        Переоопределени магического метода для строкового отображения нужных полей экземпляра класса
        """
        return self.name

    def get_shops(self):
        """
        Метод для отображения поля shops в админке django. Возвращает название магазина
        """
        return "\n".join([p.name for p in self.shops.all()])


class Product(models.Model):
    """
    Класс для создания модели товаров. Поля в модели:
    name - CharField, model - CharField, category - ForeignKey (Category)
    """
    name = models.CharField(max_length=64, verbose_name='Название продукта')
    model = models.CharField(max_length=64, verbose_name='Модель', blank=True)
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', blank=True,
                                 null=True, on_delete=models.CASCADE)

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку товаров
        в админке django
        """
        verbose_name = 'Продукт'
        verbose_name_plural = "Список продуктов"
        ordering = ('-name',)

    def __str__(self):
        """
        Переоопределени магического метода для строкового отображения нужных полей экземпляра класса
        """
        return self.name


class ShopProduct(models.Model):
    """
    Класс для создания модели товаров в конкретном магазине. Поля в модели:
    shop - ForeignKey(Shop), product - ForeignKey(Product), ext_id - PositiveIntegerField,
    quantity - PositiveIntegerField, price - PositiveIntegerField, price_rrc - PositiveIntegerField
    """
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_in_shop', blank=True,
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='Товар', related_name='product_in_shop', blank=True,
                                on_delete=models.CASCADE)
    ext_id = models.PositiveIntegerField(verbose_name='Внешний ИД')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(verbose_name='Рекомендованная розничная цена')

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку магазинов
        в админке django
        """
        verbose_name = 'Продукт в магазине'
        verbose_name_plural = 'Список продуктов в магазине'


class Parameter(models.Model):
    """
    Класс для создания модели парамметров товаров. Поле в модели:
    name - CharField
    """

    name = models.CharField(max_length=64, verbose_name='Название парамметра')

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку парамметров
        в админке django
        """
        verbose_name = 'Название парамметра'
        verbose_name_plural = 'Список парамметров'
        ordering = ('-name',)

    def __str__(self):
        """
        Переоопределени магического метода для строкового отображения нужных полей экземпляра класса
        """
        return self.name


class ProductInf(models.Model):
    """
        Класс для создания модели информации о товаре. Поля в модели:
        product - ForeignKey(Product), parameter - ForeignKey(Parameter), value - CharField
    """
    product = models.ForeignKey(Product, verbose_name='Товар', related_name='product_inf', blank=True,
                                null=True, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_inf', blank=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(max_length=128, blank=True, verbose_name='Значение')

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку
        информации о товаре в админке django
        """
        verbose_name = 'Информация о продукте'
        verbose_name_plural = 'Информацмя о продуктах'


class Contact(models.Model):
    """
    Класс для создания модели контактной информации о пользователе. Поля в модели:
    user - ForeignKey(User), country - CharField, region - CharField, zip - IntegerField, city - CharField,
    street - CharField, house - CharField, building - CharField, apartment - CharField, phone - CharField
    """
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    country = models.CharField(max_length=64, verbose_name='Страна')
    region = models.CharField(max_length=64, verbose_name='Область')
    zip = models.IntegerField(verbose_name='Почтовый индекс')
    city = models.CharField(max_length=64, verbose_name='Город')
    street = models.CharField(max_length=128, verbose_name='Улица')
    house = models.CharField(max_length=16, verbose_name='Дом', null=True)
    building = models.CharField(max_length=16, verbose_name='Строение', null=True)
    apartment = models.CharField(max_length=16, verbose_name='Квартира', null=True)
    phone = models.CharField(max_length=32, verbose_name='Телефон')

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку
        контактной информации в админке django
        """
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Список контактов пользователя"


class Order(models.Model):
    """
    Класс для создания модели заказов. Поле status принимает только значения из перемененной STATUS_CHOICES.
    Поля в модели: user - ForeignKey(User), dt - DateTimeField, status - CharField
    """
    user = models.ForeignKey(User, verbose_name='Пользователь', related_name='orders',
                             blank=True, on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    status = models.CharField(verbose_name='Статус заказа', choices=STATUS_CHOICES, max_length=16)

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку
        заказов в админке django
        """
        verbose_name = 'Заказ'
        verbose_name_plural = 'Список заказов'
        ordering = ('-dt',)

    def __str__(self):
        """
        Переоопределени магического метода для строкового отображения нужных полей экземпляра класса
        """
        return str(self.dt)


class OrderItem(models.Model):
    """
    Класс для создания модели товаров в заказе.
    Поля в модели: order - ForeignKey(Order), product_info - ForeignKey(ShopProduct), quantity - PositiveIntegerField
    """
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)
    product_info = models.ForeignKey(ShopProduct, verbose_name='Информация о продукте', related_name='ordered_items',
                                     on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку
        заказов в админке django
        """
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = 'Список заказанных позиций'

    def get_product_info(self):
        """
        Метод для отображения поля product_info в админке django. Возвращает название товара
        """
        return "\n".join([self.product_info.product.name])


class ShopFiles(models.Model):
    """
    Класс для создания модели для работы с файлами прайсов магазина.
    Поля в модели: file - FileField, shop - ForeignKey(Shop)
    """
    file = models.FileField(null=True, upload_to='uploaded_data')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True)


class ConfirmEmailToken(models.Model):
    """
        Класс для создания модели токенов подтверждения email. Метод класса generate_key, save
        Поля в модели: user - ForeignKey(User), created_at - DateTimeField, key - CharField
    """
    class Meta:
        """
        Класс для корректного отображения модели в админке django.
        Отвечает за название модели в единственном и множественном числе, а так же за стандартную сортировку
        токенов в админке django
        """
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        """ generates a pseudo random code using os.urandom and binascii.hexlify """
        return django_rest_passwordreset.tokens.get_token_generator().generate_token()

    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name=_("The User which is associated to this password reset token")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("When was this token generated")
    )

    # Key field, though it is not the primary key of the model
    key = models.CharField(
        _("Key"),
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        """
        Метод для сохранения токена
        """
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        """
        Переоопределени магического метода для строкового отображения нужных полей экземпляра класса
        """
        return "Password reset token for user {user}".format(user=self.user)
