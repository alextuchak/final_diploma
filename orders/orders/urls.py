from django.contrib import admin
from django.urls import path, include
from backend.views import ShopUpload, RegisterAccount, ConfirmAccount, LoginAccount, CategoryViewSet, ShopViewSet, \
    ProductViewSet, ShopProductViewSet, ProductInfViewSet, UserContact, AccountDetails, BasketViewSet, OrderViewSet, \
    SellerOrderViewSet
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


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
urlpatterns += [path('accounts/', include('allauth.urls'), name='social-accounts')]
urlpatterns += [path('api/schema/', SpectacularAPIView.as_view(), name='schema')]
urlpatterns += [path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui')]
urlpatterns += [path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc')]
