from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('status/<str:ref_code>', views.check_status, name='check_status'),
    path('update/<str:ref_code>', views.update_message, name='update_message'),
]
