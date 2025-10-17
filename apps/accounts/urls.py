# apps/accounts/urls.py
from django.urls import path
from .views import role_gate

urlpatterns = [
    path("", role_gate, name="role_gate"),  # HOME
]
