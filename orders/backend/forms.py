from django import forms
from backend.models import ShopFiles
from allauth.socialaccount.forms import SignupForm


class UploadFileForm(forms.ModelForm):
    """
    Класс для рзагрузки файлов обновления прайса магазина
    """
    class Meta:
        model = ShopFiles
        fields = ['file']


class SocialSignupForm(SignupForm):
    """
    Класс для активации пользователей авторизованных через социальные сети
    """

    def save(self, request):
        user = super(SocialSignupForm, self).save(request)
        user.is_active = True
        user.save()
        return user