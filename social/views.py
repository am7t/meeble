from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from .models import Comment, Post, Reaction

PAGE_SIZE = 20
MAX_COMMENT_LENGTH = 500


def _authentication_error():
    return JsonResponse({"error": "Sign in to use your local feed."}, status=401)


def _visible_post(user, post_id):
    visible_posts = Post.objects.filter(
        Q(author=user)
        | Q(visibility=Post.Visibility.PUBLIC)
        | Q(
            visibility=Post.Visibility.FOLLOWERS,
            author__followers__follower=user,
        )
    )
    return get_object_or_404(visible_posts.distinct(), pk=post_id)


def _annotated_posts(user):
    return Post.objects.select_related("author__profile").annotate(
        _api_reaction_count=Count("reactions", distinct=True),
        _api_comment_count=Count("comments", distinct=True),
        _api_liked=Exists(Reaction.objects.filter(post_id=OuterRef("pk"), user=user)),
    )


def _serialize_comment(comment):
    return {
        "id": comment.pk,
        "name": comment.author.profile.display_name,
        "handle": comment.author.profile.handle,
        "text": comment.body,
    }


def _serialize_post(post, user):
    comments = post.comments.select_related("author__profile").order_by("-created_at", "-pk")[:20]
    reaction_count = getattr(post, "_api_reaction_count", None)
    if reaction_count is None:
        reaction_count = post.reactions.count()
    comment_count = getattr(post, "_api_comment_count", None)
    if comment_count is None:
        comment_count = post.comments.count()
    liked = getattr(post, "_api_liked", None)
    if liked is None:
        liked = post.reactions.filter(user=user).exists()
    return {
        "id": f"db-{post.pk}",
        "server_id": post.pk,
        "author": post.author.profile.display_name,
        "handle": f"@{post.author.profile.handle}",
        "avatar": None,
        "time": post.created_at.isoformat(),
        "caption": post.body,
        "art": "custom",
        "art_label": "",
        "likes": reaction_count,
        "liked": liked,
        "comments": [_serialize_comment(comment) for comment in reversed(list(comments))],
        "comment_count": comment_count,
        "can_delete": post.author_id == user.pk,
    }


def _visible_feed_queryset(user):
    return (
        _annotated_posts(user)
        .filter(
            Q(author=user)
            | Q(visibility=Post.Visibility.PUBLIC)
            | Q(
                visibility=Post.Visibility.FOLLOWERS,
                author__followers__follower=user,
            )
        )
        .distinct()
        .order_by("-created_at", "-pk")
    )


@require_GET
def feed(request):
    if not request.user.is_authenticated:
        return _authentication_error()
    try:
        page_number = int(request.GET.get("page", "1"))
    except ValueError:
        return JsonResponse({"error": "Page must be a positive number."}, status=400)
    if page_number < 1:
        return JsonResponse({"error": "Page must be a positive number."}, status=400)

    page = Paginator(_visible_feed_queryset(request.user), PAGE_SIZE).get_page(page_number)
    return JsonResponse(
        {
            "results": [_serialize_post(post, request.user) for post in page.object_list],
            "next_page": page.next_page_number() if page.has_next() else None,
        }
    )


@require_POST
def create_post(request):
    if not request.user.is_authenticated:
        return _authentication_error()
    body = request.POST.get("body", "").strip()
    visibility = request.POST.get("visibility", Post.Visibility.PUBLIC)
    if not body or len(body) > 500:
        return JsonResponse({"error": "Write a post between 1 and 500 characters."}, status=400)
    if visibility not in Post.Visibility.values:
        return JsonResponse({"error": "Choose a supported post visibility."}, status=400)

    post = Post.objects.create(author=request.user, body=body, visibility=visibility)
    post = _annotated_posts(request.user).get(pk=post.pk)
    return JsonResponse(_serialize_post(post, request.user), status=201)


@require_POST
def toggle_reaction(request, post_id):
    if not request.user.is_authenticated:
        return _authentication_error()
    post = _visible_post(request.user, post_id)
    reaction = Reaction.objects.filter(post=post, user=request.user).first()
    if reaction:
        reaction.delete()
        liked = False
    else:
        try:
            with transaction.atomic():
                Reaction.objects.create(post=post, user=request.user)
            liked = True
        except IntegrityError:
            liked = Reaction.objects.filter(post=post, user=request.user).exists()
    return JsonResponse({"liked": liked, "count": post.reactions.count()})


@require_POST
def create_comment(request, post_id):
    if not request.user.is_authenticated:
        return _authentication_error()
    post = _visible_post(request.user, post_id)
    body = request.POST.get("body", "").strip()
    if not body or len(body) > MAX_COMMENT_LENGTH:
        return JsonResponse(
            {"error": f"Write a comment between 1 and {MAX_COMMENT_LENGTH} characters."},
            status=400,
        )
    comment = Comment.objects.create(post=post, author=request.user, body=body)
    return JsonResponse(
        {
            "comment": _serialize_comment(comment),
            "comment_count": post.comments.count(),
        },
        status=201,
    )


@require_POST
def delete_post(request, post_id):
    if not request.user.is_authenticated:
        return _authentication_error()
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    post.delete()
    return HttpResponse(status=204)
