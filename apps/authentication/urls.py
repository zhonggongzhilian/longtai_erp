# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path
from .views import login_view, register_user
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('auth_login/', login_view, name="login"),
    path('auth_register/', register_user, name="register"),
    path("auth_logout/", LogoutView.as_view(), name="logout")
]
