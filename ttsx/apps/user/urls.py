from django.urls import path
from apps.user import views
from apps.user.views import *

urlpatterns = [
    # path('register/', views.register, name='register'),
    path('register/', RegisterView.as_view(), name='register'),
    path('active/<str:token>/', Active.as_view(), name='active'),
    path('login/', Login.as_view(), name='login'),
]