from django.urls import path
from apps.goods.views import *


urlpatterns = [
    path('index/', IndexView.as_view(), name='index'),
    path('detail/<int:goods_id>', DetailView.as_view(), name='detail')
]