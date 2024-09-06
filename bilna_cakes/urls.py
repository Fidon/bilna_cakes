from django.contrib import admin
from django.urls import path
from . import views as v

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bilna/card/', v.vcard_page, name='virtual_card'),
]
