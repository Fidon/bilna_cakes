from django.urls import path
from . import views as v

urlpatterns = [
    path('dashboard/', v.dashboard_page, name='dashboard_page'),
    path('orders/', v.orders_page, name='orders_page'),
    path('orders/actions/', v.orders_actions, name='order_actions'),
    path('orders/<int:order_id>/', v.order_details, name='order_details'),
    path('purchases/', v.purchases_page, name='purchases_page'),
    path('purchases/actions/', v.purchases_actions, name='purchases_actions'),
    path('purchases/<int:purchase_id>/', v.purchase_details, name='purchase_details'),
]
