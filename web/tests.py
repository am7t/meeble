from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from social.models import Follow, Post


class LocalAppViewsTests(TestCase):
    def test_home_serves_the_showcase(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good things happen")
        self.assertContains(response, "/static/web/app.js")

    def test_health_check_reports_local_service(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "meeble-local"})

    def test_signed_in_home_exposes_session_and_csrf_context_to_the_ui(self):
        user = get_user_model().objects.create_user("amelia@example.com", "safe demo password")
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertContains(response, 'data-authenticated="true"')
        self.assertContains(response, 'data-display-name="Amelia"')
        self.assertContains(response, 'name="csrf-token" content="')
        self.assertContains(response, 'feed: "/api/feed/"')
        self.assertContains(response, 'people: "/api/people/"')
        self.assertContains(response, 'data-feed-filter="following"')
        self.assertContains(response, 'data-profile-url-template="/profiles/__handle__/"')


class PublicProfileTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user("jules@example.com", "safe demo password")
        self.viewer = User.objects.create_user("amelia@example.com", "safe demo password")
        self.profile = self.owner.profile
        self.profile.handle = "jules_chen"
        self.profile.display_name = "Jules Chen"
        self.profile.bio = "A little outside, a little in."
        self.profile.customization = {"theme": "lilac", "layout": "airy"}
        self.profile.save()
        self.public = Post.objects.create(
            author=self.owner, body="A public little thought", visibility=Post.Visibility.PUBLIC
        )
        self.followers = Post.objects.create(
            author=self.owner, body="For my close circle", visibility=Post.Visibility.FOLLOWERS
        )
        self.private = Post.objects.create(
            author=self.owner, body="Just for me", visibility=Post.Visibility.PRIVATE
        )
        self.url = reverse("public-profile", kwargs={"handle": self.profile.handle})

    def test_anonymous_profile_shows_public_details_and_public_posts_only(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jules Chen")
        self.assertContains(response, "@jules_chen")
        self.assertContains(response, "A little outside, a little in.")
        self.assertContains(response, "A public little thought")
        self.assertNotContains(response, "For my close circle")
        self.assertNotContains(response, "Just for me")
        self.assertNotContains(response, self.owner.email)
        self.assertContains(response, "Sign in to follow")

    def test_followers_see_followers_posts_but_only_owner_sees_private_posts(self):
        Follow.objects.create(follower=self.viewer, followed=self.owner)
        self.client.force_login(self.viewer)

        follower_view = self.client.get(self.url)

        self.assertContains(follower_view, "For my close circle")
        self.assertNotContains(follower_view, "Just for me")
        self.assertContains(
            follower_view, f'data-follow-url="/api/people/{self.owner.pk}/follow/toggle/"'
        )

        self.client.force_login(self.owner)
        owner_view = self.client.get(self.url)
        self.assertContains(owner_view, "A public little thought")
        self.assertContains(owner_view, "For my close circle")
        self.assertContains(owner_view, "Just for me")
        self.assertContains(owner_view, "Edit profile")
        self.assertNotContains(owner_view, self.owner.email)

    def test_profile_handle_lookup_is_case_insensitive_and_missing_profiles_are_404(self):
        response = self.client.get(reverse("public-profile", kwargs={"handle": "JULES_CHEN"}))

        self.assertEqual(response.status_code, 200)
        missing = self.client.get(reverse("public-profile", kwargs={"handle": "unknown_user"}))
        self.assertEqual(missing.status_code, 404)

    def test_public_profile_escapes_user_text_and_paginates_visible_posts(self):
        self.profile.bio = '<script>alert("hello")</script>'
        self.profile.save()
        Post.objects.bulk_create(
            [Post(author=self.owner, body=f"A public moment {number}") for number in range(12)]
        )

        first_page = self.client.get(self.url)
        second_page = self.client.get(self.url, {"page": "2"})

        self.assertContains(first_page, "&lt;script&gt;alert(&quot;hello&quot;)&lt;/script&gt;")
        self.assertEqual(first_page.context["post_count"], 13)
        self.assertContains(first_page, "Older posts")
        self.assertEqual(len(first_page.context["posts"].object_list), 12)
        self.assertEqual(len(second_page.context["posts"].object_list), 1)
        self.assertNotContains(first_page, "Just for me")
