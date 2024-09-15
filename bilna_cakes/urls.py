from django.contrib import admin
from django.urls import path, include
from . import views as v

handler404 = 'bilna_cakes.views.error_404'
handler403 = 'bilna_cakes.views.error_403'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bilnacakes/', v.vcard_page, name='virtual_card'),
    path('', v.index_page, name='index_page'),
    path('shop/', include('apps.shop.urls')),
    path('users/', include('apps.users.urls')),
]
