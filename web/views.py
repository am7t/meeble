from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from accounts.models import Profile
from social.models import Follow, Post


def home(request):
    return render(request, "web/index.html")


def health(request):
    return JsonResponse({"status": "ok", "service": "meeble-local"})


@require_GET
def public_profile(request, handle):
    profile = get_object_or_404(
        Profile.objects.select_related("user"), handle__iexact=handle, user__is_active=True
    )
    viewer = request.user
    is_owner = viewer.is_authenticated and viewer.pk == profile.user_id
    is_following = (
        viewer.is_authenticated
        and not is_owner
        and Follow.objects.filter(follower=viewer, followed_id=profile.user_id).exists()
    )

    visible_posts = Post.objects.filter(author_id=profile.user_id)
    if not is_owner:
        allowed_visibility = [Post.Visibility.PUBLIC]
        if is_following:
            allowed_visibility.append(Post.Visibility.FOLLOWERS)
        visible_posts = visible_posts.filter(visibility__in=allowed_visibility)

    posts = visible_posts.annotate(
        reaction_count=Count("reactions", distinct=True),
        comment_count=Count("comments", distinct=True),
    ).order_by("-created_at", "-pk")
    page = Paginator(posts, 12).get_page(request.GET.get("page", 1))
    return render(
        request,
        "web/public_profile.html",
        {
            "profile": profile,
            "posts": page,
            "post_count": posts.count(),
            "follower_count": profile.user.followers.count(),
            "following_count": profile.user.following.count(),
            "is_owner": is_owner,
            "is_following": is_following,
        },
    )
