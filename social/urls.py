from django.urls import path
from . import views

app_name = "social"

urlpatterns = [
    path("feed/", views.feed, name="feed"),
    path("posts/", views.create_post, name="create-post"),
    path("posts/<int:post_id>/reactions/toggle/", views.toggle_reaction, name="toggle-reaction"),
    path("posts/<int:post_id>/comments/", views.create_comment, name="create-comment"),
    path("posts/<int:post_id>/delete/", views.delete_post, name="delete-post"),
    path("posts/<int:post_id>/edit/", views.edit_post, name="edit-post"),
]
