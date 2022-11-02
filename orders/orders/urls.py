from django.contrib import admin
from django.urls import path
from backend.views import ShopUpload, RegisterAccount, ConfirmAccount, LoginAccount, CategoryViewSet, ShopViewSet, \
    ProductViewSet, ShopProductViewSet, ProductInfViewSet, UserContact, AccountDetails, BasketViewSet, OrderViewSet, \
    SellerOrderViewSet
from rest_framework.routers import DefaultRouter

admin.site.site_header = 'Сервис заказов'
admin.site.index_title = 'База данных'

r = DefaultRouter()
r.register('categories', CategoryViewSet)
r.register('shops', ShopViewSet)
r.register('products', ProductViewSet)
r.register('products_in_shop', ShopProductViewSet)
r.register('product_inf', ProductInfViewSet)
r.register('basket', BasketViewSet)
r.register('order/customer', OrderViewSet)
r.register('order/seller', SellerOrderViewSet)
urlpatterns = r.urls
urlpatterns += [path('admin/', admin.site.urls)]
urlpatterns += [path('shop/upload', ShopUpload.as_view(), name='shop-upload')]
urlpatterns += [path('user/register', RegisterAccount.as_view(), name='user-register')]
urlpatterns += [path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm')]
urlpatterns += [path('user/login', LoginAccount.as_view(), name='user-login')]
urlpatterns += [path('user/contact', UserContact.as_view(), name='user-contact')]
urlpatterns += [path('user/info', AccountDetails.as_view(), name='user-info')]

