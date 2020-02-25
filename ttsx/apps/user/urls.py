from django.urls import path
from apps.user import views
from apps.user.views import *
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # path('register/', views.register, name='register'),
    path('register/', RegisterView.as_view(), name='register'),
    path('active/<str:token>/', Active.as_view(), name='active'),
    path('login/', Login.as_view(), name='login'),
    path('', login_required(UserInfo.as_view()), name='user'),
    path('order/', login_required(UserOrder.as_view()), name='order'),
    path('address/', login_required(UserAddress.as_view()), name='address'),
]