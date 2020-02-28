from django.urls import path
from apps.goods.views import *


urlpatterns = [
    path('index/', IndexView.as_view(), name='index'),
    path('detail/<int:goods_id>', DetailView.as_view(), name='detail'),
    path('goods_list/<str:category_id>/<int:page>', ListView.as_view(), name='goods_list')
]