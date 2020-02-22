from django.urls import path
from apps.user import views
from apps.user.views import RegisterView

urlpatterns = [
    # path('register/', views.register, name='register'),
    path('register/', RegisterView.as_view(), name='register')
]