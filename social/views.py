import warnings
from datetime import timedelta
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from .models import Comment, Follow, Post, Reaction, Story

PAGE_SIZE = 20
MAX_COMMENT_LENGTH = 500
MAX_STORY_CAPTION_LENGTH = 160
MAX_STORY_IMAGE_BYTES = 8 * 1024 * 1024
MAX_STORY_PIXELS = 20_000_000
MAX_STORY_EDGE = 2400
STORY_LIFETIME = timedelta(hours=24)
STORY_IMAGE_FORMATS = ("JPEG", "PNG", "WEBP")


def _authentication_error():
    return JsonResponse({"error": "Sign in to use your local feed."}, status=401)


def _sanitize_story_image(upload):
    if upload.size > MAX_STORY_IMAGE_BYTES:
        raise ValidationError("Choose an image under 8 MB.")
    try:
        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload, formats=STORY_IMAGE_FORMATS) as source:
                if source.width * source.height > MAX_STORY_PIXELS:
                    raise ValidationError("Choose an image with 20 megapixels or fewer.")
                if getattr(source, "n_frames", 1) != 1:
                    raise ValidationError("Animated images are not supported for stories yet.")
                source.verify()

        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload, formats=STORY_IMAGE_FORMATS) as source:
                source.load()
                image = ImageOps.exif_transpose(source)
                if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                    transparent = image.convert("RGBA")
                    flattened = Image.new("RGB", transparent.size, "white")
                    flattened.paste(transparent, mask=transparent.getchannel("A"))
                    image = flattened
                else:
                    image = image.convert("RGB")
                image.thumbnail((MAX_STORY_EDGE, MAX_STORY_EDGE), Image.Resampling.LANCZOS)
                output = BytesIO()
                image.save(output, "JPEG", quality=88, optimize=True, exif=b"", icc_profile=None)
        return ContentFile(output.getvalue(), name="story.jpg")
    except ValidationError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        UnidentifiedImageError,
        ValueError,
    ) as error:
        raise ValidationError("Choose a readable JPEG, PNG, or WebP image.") from error


def _visible_stories(user):
    return (
        Story.objects.select_related("author__profile")
        .filter(expires_at__gt=timezone.now(), author__is_active=True)
        .filter(
            Q(author=user)
            | Q(visibility=Story.Visibility.PUBLIC)
            | Q(
                visibility=Story.Visibility.FOLLOWERS,
                author__followers__follower=user,
            )
        )
        .distinct()
        .order_by("-created_at", "-pk")
    )


def _serialize_story(story, user):
    return {
        "id": story.pk,
        "author_id": story.author_id,
        "author": story.author.profile.display_name,
        "handle": f"@{story.author.profile.handle}",
        "caption": story.caption,
        "created_at": story.created_at.isoformat(),
        "expires_at": story.expires_at.isoformat(),
        "visibility": story.visibility,
        "image_url": reverse("social:story-image", args=[story.pk]),
        "can_delete": story.author_id == user.pk,
    }


def _visible_post(user, post_id):
    visible_posts = Post.objects.filter(author__is_active=True).filter(
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
        "can_edit": post.author_id == user.pk,
        "edited": post.updated_at > post.created_at,
    }


def _visible_feed_queryset(user, following_only=False):
    posts = _annotated_posts(user).filter(author__is_active=True)
    if following_only:
        posts = posts.filter(
            author__followers__follower=user,
            visibility__in=[Post.Visibility.PUBLIC, Post.Visibility.FOLLOWERS],
        )
    else:
        posts = posts.filter(
            Q(author=user)
            | Q(visibility=Post.Visibility.PUBLIC)
            | Q(
                visibility=Post.Visibility.FOLLOWERS,
                author__followers__follower=user,
            )
        )
    return posts.distinct().order_by("-created_at", "-pk")


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
    feed_filter = request.GET.get("filter", "for-you")
    if feed_filter not in {"for-you", "following"}:
        return JsonResponse({"error": "Choose a supported feed filter."}, status=400)

    page = Paginator(
        _visible_feed_queryset(request.user, following_only=feed_filter == "following"), PAGE_SIZE
    ).get_page(page_number)
    return JsonResponse(
        {
            "results": [_serialize_post(post, request.user) for post in page.object_list],
            "next_page": page.next_page_number() if page.has_next() else None,
        }
    )


@require_GET
def people(request):
    if not request.user.is_authenticated:
        return _authentication_error()
    try:
        page_number = int(request.GET.get("page", "1"))
    except ValueError:
        return JsonResponse({"error": "Page must be a positive number."}, status=400)
    if page_number < 1:
        return JsonResponse({"error": "Page must be a positive number."}, status=400)

    User = get_user_model()
    people_page = Paginator(
        User.objects.filter(is_active=True)
        .exclude(pk=request.user.pk)
        .select_related("profile")
        .annotate(
            _api_following=Exists(
                Follow.objects.filter(follower=request.user, followed_id=OuterRef("pk"))
            ),
            _api_follower_count=Count("followers", distinct=True),
        )
        .order_by("profile__display_name", "pk"),
        PAGE_SIZE,
    ).get_page(page_number)
    return JsonResponse(
        {
            "results": [
                {
                    "id": user.pk,
                    "name": user.profile.display_name,
                    "handle": f"@{user.profile.handle}",
                    "following": user._api_following,
                    "follower_count": user._api_follower_count,
                }
                for user in people_page.object_list
            ],
            "next_page": people_page.next_page_number() if people_page.has_next() else None,
        }
    )


@require_POST
def toggle_follow(request, user_id):
    if not request.user.is_authenticated:
        return _authentication_error()
    User = get_user_model()
    target = get_object_or_404(
        User.objects.filter(is_active=True).exclude(pk=request.user.pk), pk=user_id
    )
    follow = Follow.objects.filter(follower=request.user, followed=target).first()
    if follow:
        follow.delete()
        following = False
    else:
        try:
            with transaction.atomic():
                Follow.objects.create(follower=request.user, followed=target)
            following = True
        except IntegrityError:
            following = Follow.objects.filter(follower=request.user, followed=target).exists()
    return JsonResponse(
        {
            "following": following,
            "follower_count": target.followers.count(),
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


@require_POST
def edit_post(request, post_id):
    if not request.user.is_authenticated:
        return _authentication_error()
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    body = request.POST.get("body", "").strip()
    if not body or len(body) > 500:
        return JsonResponse({"error": "Write a post between 1 and 500 characters."}, status=400)

    post.body = body
    post.save(update_fields=["body", "updated_at"])
    post = _annotated_posts(request.user).get(pk=post.pk)
    return JsonResponse(_serialize_post(post, request.user))


@require_GET
def stories(request):
    if not request.user.is_authenticated:
        return _authentication_error()
    try:
        page_number = int(request.GET.get("page", "1"))
    except ValueError:
        return JsonResponse({"error": "Page must be a positive number."}, status=400)
    if page_number < 1:
        return JsonResponse({"error": "Page must be a positive number."}, status=400)

    page = Paginator(_visible_stories(request.user), PAGE_SIZE).get_page(page_number)
    return JsonResponse(
        {
            "results": [_serialize_story(story, request.user) for story in page.object_list],
            "next_page": page.next_page_number() if page.has_next() else None,
        }
    )


@require_POST
def create_story(request):
    if not request.user.is_authenticated:
        return _authentication_error()
    upload = request.FILES.get("image")
    if upload is None:
        return JsonResponse({"error": "Choose a photo for your story."}, status=400)
    caption = request.POST.get("caption", "").strip()
    if len(caption) > MAX_STORY_CAPTION_LENGTH:
        return JsonResponse(
            {"error": f"Keep your story caption under {MAX_STORY_CAPTION_LENGTH} characters."},
            status=400,
        )
    visibility = request.POST.get("visibility", Story.Visibility.PUBLIC)
    if visibility not in Story.Visibility.values:
        return JsonResponse({"error": "Choose a supported story audience."}, status=400)
    try:
        image = _sanitize_story_image(upload)
    except ValidationError as error:
        return JsonResponse({"error": error.messages[0]}, status=400)

    story = Story(
        author=request.user,
        caption=caption,
        visibility=visibility,
        expires_at=timezone.now() + STORY_LIFETIME,
    )
    story.image.save("story.jpg", image, save=False)
    try:
        with transaction.atomic():
            story.save()
    except Exception:
        story.image.delete(save=False)
        raise
    return JsonResponse(_serialize_story(story, request.user), status=201)


@require_GET
def story_image(request, story_id):
    if not request.user.is_authenticated:
        return _authentication_error()
    story = get_object_or_404(_visible_stories(request.user), pk=story_id)
    try:
        image_file = story.image.open("rb")
    except OSError as error:
        raise Http404("Story image is unavailable.") from error
    response = FileResponse(image_file, content_type="image/jpeg")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Cross-Origin-Resource-Policy"] = "same-origin"
    return response


@require_POST
def delete_story(request, story_id):
    if not request.user.is_authenticated:
        return _authentication_error()
    story = get_object_or_404(Story, pk=story_id, author=request.user)
    story.delete()
    return HttpResponse(status=204)
