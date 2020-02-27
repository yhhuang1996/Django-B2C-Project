from django.urls import path
from apps.goods.views import *


urlpatterns = [
    path('', IndexView.as_view(), name='index')
]