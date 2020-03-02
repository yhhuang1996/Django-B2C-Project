from django.urls import path
from apps.cart.views import *

urlpatterns = [
    path('add/', CartAddView.as_view(), name='cart_add'),
    path('', CartView.as_view(), name='cart'),
    path('cart_update/', CartUpdateView.as_view(), name='cart_update'),

]