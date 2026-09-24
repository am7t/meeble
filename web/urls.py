from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("profiles/<str:handle>/", views.public_profile, name="public-profile"),
    path("health/", views.health, name="health"),
]
