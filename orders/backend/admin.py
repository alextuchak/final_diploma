from django.contrib import admin
from .models import *
from django.db.models import QuerySet


# Register your models here.

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'url', 'seller', 'is_work']
    list_editable = ['name', 'url', 'is_work']
    ordering = ['id']
    list_per_page = 10
    search_fields = ['name']
    list_filter = ['is_work', 'url']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'get_shops']
    list_editable = ['name']
    ordering = ['id', 'name']
    list_per_page = 10
    search_fields = ['name']
    list_filter = ['name',]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'model', 'category']
    list_editable = ['name', 'model']
    ordering = ['id', 'name', 'category']
    list_per_page = 10
    search_fields = ['name', 'model']
    list_filter = ['name', 'model', 'category']


@admin.register(ShopProduct)
class ShopProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'shop', 'product', 'ext_id', 'quantity', 'price', 'price_rrc']
    list_editable = ['ext_id', 'quantity', 'price', 'price_rrc']
    ordering = ['id', 'shop', 'product', 'price', 'price_rrc']
    list_per_page = 10
    search_fields = ['product', 'shop']
    list_filter = ['shop', 'product']


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_editable = ['name']
    ordering = ['id']
    list_per_page = 10
    search_fields = ['name']


@admin.register(ProductInf)
class ProductInfAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'parameter', 'value']
    list_editable = ['value']
    ordering = ['id', 'product']
    list_per_page = 10
    search_fields = ['product']
    list_filter = ['product', 'parameter']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'country', 'region', 'zip', 'city', 'street', 'house', 'building', 'apartment',
                    'phone']
    list_editable = ['user', 'country', 'region', 'zip', 'city', 'street', 'house', 'building', 'apartment',
                     'phone']
    ordering = ['id']
    list_per_page = 10
    search_fields = ['user', 'phone', 'city']
    list_filter = ['country', 'city']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'dt', 'status']
    list_editable = ['status']
    ordering = ['id', 'user', 'status']
    list_per_page = 10
    actions = ['set_confirmed', 'set_assembled', 'set_sent', 'set_delivered', 'set_canceled']
    search_fields = ['status', 'user']
    list_filter = ['status']

    @admin.action(description="Установить статус заказа Подтвержден")
    def set_confirmed(self, request, qs: QuerySet):
        count_updated = qs.update(status="confirmed")
        self.message_user(
            request,
            f"Было обновлено {count_updated} записей"
        )

    @admin.action(description="Установить статус заказа Собран")
    def set_assembled(self, request, qs: QuerySet):
        count_updated = qs.update(status="assembled")
        self.message_user(
            request,
            f"Было обновлено {count_updated} записей"
        )

    @admin.action(description="Установить статус заказа Отправлен")
    def set_sent(self, request, qs: QuerySet):
        count_updated = qs.update(status="sent")
        self.message_user(
            request,
            f"Было обновлено {count_updated} записей"
        )

    @admin.action(description="Установить статус заказа Доставлен")
    def set_delivered(self, request, qs: QuerySet):
        count_updated = qs.update(status="delivered")
        self.message_user(
            request,
            f"Было обновлено {count_updated} записей"
        )

    @admin.action(description="Установить статус заказа Отменен")
    def set_canceled(self, request, qs: QuerySet):
        count_updated = qs.update(status="canceled")
        self.message_user(
            request,
            f"Было обновлено {count_updated} записей"
        )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'get_product_info', 'quantity']
    list_editable = ['quantity']
    ordering = ['id']
    list_per_page = 10
    search_fields = ['order', 'get_product_info']

