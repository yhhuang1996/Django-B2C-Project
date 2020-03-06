from django.urls import path
from apps.order.views import *

urlpatterns = [
    path('place_order/', PlaceOrderView.as_view(), name='place_order'),
    path('order_commit/', OrderCommitView.as_view(), name='order_commit'),
    path('order_pay/', OrderPayView.as_view(), name='order_pay'),
    path('order_check/', OrderCheckView.as_view(), name='order_check'),
    path('comment/<int:order_id>', CommentView.as_view(), name='comment'),
]