from django.urls import path
from apps.order.views import *

urlpatterns = [
    path('place_order/', PlaceOrderView.as_view(), name='place_order'),
    path('order_commit/', OrderCommitView.as_view(), name='order_commit'),
    path('order_pay/', OrderPayView.as_view(), name='order_pay'),
]