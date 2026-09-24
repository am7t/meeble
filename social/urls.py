from django.urls import path
from . import views

app_name = "social"

urlpatterns = [
    path("feed/", views.feed, name="feed"),
    path("people/", views.people, name="people"),
    path("people/<int:user_id>/follow/toggle/", views.toggle_follow, name="toggle-follow"),
    path("stories/", views.stories, name="stories"),
    path("stories/create/", views.create_story, name="create-story"),
    path("stories/<int:story_id>/image/", views.story_image, name="story-image"),
    path("stories/<int:story_id>/delete/", views.delete_story, name="delete-story"),
    path("posts/", views.create_post, name="create-post"),
    path("posts/<int:post_id>/reactions/toggle/", views.toggle_reaction, name="toggle-reaction"),
    path("posts/<int:post_id>/comments/", views.create_comment, name="create-comment"),
    path("posts/<int:post_id>/delete/", views.delete_post, name="delete-post"),
    path("posts/<int:post_id>/edit/", views.edit_post, name="edit-post"),
]
