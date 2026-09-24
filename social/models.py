from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Length
from django.db.models.lookups import GreaterThanOrEqual, LessThanOrEqual


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "followed"], name="follow_pair_unique"),
            models.CheckConstraint(
                condition=~Q(follower=F("followed")), name="follow_no_self_follow"
            ),
        ]
        indexes = [
            models.Index(fields=["followed", "created_at"], name="follow_target_created_idx")
        ]


class Post(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        FOLLOWERS = "followers", "Followers"
        PRIVATE = "private", "Only me"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    body = models.CharField(max_length=500)
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=GreaterThanOrEqual(Length("body"), 1)
                & LessThanOrEqual(Length("body"), 500),
                name="post_body_length_valid",
            ),
            models.CheckConstraint(
                condition=Q(visibility__in=["public", "followers", "private"]),
                name="post_visibility_valid",
            ),
        ]
        indexes = [models.Index(fields=["-created_at", "id"], name="post_feed_order_idx")]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=GreaterThanOrEqual(Length("body"), 1)
                & LessThanOrEqual(Length("body"), 500),
                name="comment_body_length_valid",
            ),
        ]
        indexes = [models.Index(fields=["post", "created_at"], name="comment_post_created_idx")]


class Reaction(models.Model):
    class Kind(models.TextChoices):
        LIKE = "like", "Like"
        LOVE = "love", "Love"
        CELEBRATE = "celebrate", "Celebrate"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reactions"
    )
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.LIKE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="reaction_user_post_unique"),
            models.CheckConstraint(
                condition=Q(kind__in=["like", "love", "celebrate"]),
                name="reaction_kind_valid",
            ),
        ]
        indexes = [models.Index(fields=["post", "created_at"], name="reaction_post_created_idx")]
