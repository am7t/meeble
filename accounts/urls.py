from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("sign-up/", views.register, name="register"),
    path("sign-in/", views.sign_in, name="login"),
    path("sign-out/", views.sign_out, name="logout"),
    path("profile/", views.profile_edit, name="profile"),
]
