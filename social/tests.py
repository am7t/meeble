from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.urls import reverse
from django.test import Client
from django.test import TestCase
from accounts.models import Profile
from .models import Comment, Follow, Post, Reaction


class SocialSchemaTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.amelia = User.objects.create_user("amelia@example.com", "safe demo password")
        self.jules = User.objects.create_user("jules@example.com", "safe demo password")
        Profile.objects.filter(user=self.amelia).update(handle="amelia", display_name="Amelia Rose")
        Profile.objects.filter(user=self.jules).update(handle="jules", display_name="Jules Parker")
        self.amelia.profile.refresh_from_db()
        self.jules.profile.refresh_from_db()
        self.post = Post.objects.create(author=self.amelia, body="A small happy moment")

    def test_sqlite_enforces_foreign_keys(self):
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys")
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_profile_handles_are_case_insensitively_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.filter(user=self.jules).update(handle="AMELIA")

    def test_follow_relationship_is_unique_and_cannot_target_self(self):
        Follow.objects.create(follower=self.amelia, followed=self.jules)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(follower=self.amelia, followed=self.jules)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(follower=self.jules, followed=self.jules)

    def test_reaction_is_unique_per_user_and_post_and_comment_is_related(self):
        Reaction.objects.create(user=self.jules, post=self.post)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reaction.objects.create(user=self.jules, post=self.post, kind=Reaction.Kind.LOVE)
        comment = Comment.objects.create(author=self.jules, post=self.post, body="Lovely!")
        self.assertEqual(self.post.comments.get(), comment)

    def test_post_and_comment_reject_empty_bodies_at_the_database_layer(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Post.objects.create(author=self.amelia, body="")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Post.objects.create(author=self.amelia, body="x" * 501)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Comment.objects.create(author=self.jules, post=self.post, body="")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Comment.objects.create(author=self.jules, post=self.post, body="x" * 501)

    def test_invalid_post_visibility_and_reaction_kind_are_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Post.objects.create(author=self.amelia, body="Hello", visibility="unlisted")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reaction.objects.create(user=self.jules, post=self.post, kind="surprise")

    def test_profile_field_lengths_are_constrained_in_sqlite(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.filter(user=self.jules).update(handle="a")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.filter(user=self.jules).update(display_name="d" * 41)

    def test_deleting_an_account_cascades_its_social_records(self):
        self.amelia.delete()
        self.assertFalse(Profile.objects.filter(handle="amelia").exists())
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())


class FeedAPITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.amelia = User.objects.create_user("amelia@example.com", "safe demo password")
        self.jules = User.objects.create_user("jules@example.com", "safe demo password")
        Profile.objects.filter(user=self.amelia).update(handle="amelia", display_name="Amelia Rose")
        Profile.objects.filter(user=self.jules).update(handle="jules", display_name="Jules Parker")
        self.amelia.profile.refresh_from_db()
        self.jules.profile.refresh_from_db()
        self.feed_url = reverse("social:feed")
        self.create_url = reverse("social:create-post")

    def test_feed_api_requires_authentication(self):
        response = self.client.get(self.feed_url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "Sign in to use your local feed.")

    def test_create_post_uses_signed_in_owner_and_validates_body(self):
        self.client.force_login(self.amelia)
        response = self.client.post(
            self.create_url,
            {"body": "  A new little moment  ", "author": self.jules.pk},
        )

        self.assertEqual(response.status_code, 201)
        post = Post.objects.get()
        self.assertEqual(post.author, self.amelia)
        self.assertEqual(post.body, "A new little moment")
        self.assertEqual(response.json()["server_id"], post.pk)
        self.assertEqual(response.json()["author"], self.amelia.profile.display_name)
        self.assertEqual(response.json()["likes"], 0)
        self.assertEqual(response.json()["comment_count"], 0)

        for body in (" ", "x" * 501):
            rejected = self.client.post(self.create_url, {"body": body})
            self.assertEqual(rejected.status_code, 400)
        self.assertEqual(Post.objects.count(), 1)

    def test_feed_respects_public_followers_and_private_visibility(self):
        public_post = Post.objects.create(
            author=self.jules, body="Public moment", visibility=Post.Visibility.PUBLIC
        )
        followers_post = Post.objects.create(
            author=self.jules, body="For followers", visibility=Post.Visibility.FOLLOWERS
        )
        private_post = Post.objects.create(
            author=self.jules, body="Just for me", visibility=Post.Visibility.PRIVATE
        )
        self.client.force_login(self.amelia)

        response = self.client.get(self.feed_url)
        ids = {item["server_id"] for item in response.json()["results"]}
        self.assertIn(public_post.pk, ids)
        self.assertNotIn(followers_post.pk, ids)
        self.assertNotIn(private_post.pk, ids)

        Follow.objects.create(follower=self.amelia, followed=self.jules)
        followed_response = self.client.get(self.feed_url)
        followed_ids = {item["server_id"] for item in followed_response.json()["results"]}
        self.assertIn(followers_post.pk, followed_ids)
        self.assertNotIn(private_post.pk, followed_ids)

        own_post = Post.objects.create(author=self.amelia, body="My own note")
        following_response = self.client.get(self.feed_url, {"filter": "following"})
        following_ids = {item["server_id"] for item in following_response.json()["results"]}
        self.assertIn(public_post.pk, following_ids)
        self.assertIn(followers_post.pk, following_ids)
        self.assertNotIn(private_post.pk, following_ids)
        self.assertNotIn(own_post.pk, following_ids)
        self.assertEqual(self.client.get(self.feed_url, {"filter": "unknown"}).status_code, 400)

    def test_people_directory_returns_public_fields_and_excludes_current_user(self):
        people_url = reverse("social:people")
        self.assertEqual(self.client.get(people_url).status_code, 401)
        self.client.force_login(self.amelia)

        response = self.client.get(people_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)
        person = response.json()["results"][0]
        self.assertEqual(person["id"], self.jules.pk)
        self.assertEqual(person["name"], "Jules Parker")
        self.assertEqual(person["handle"], "@jules")
        self.assertFalse(person["following"])
        self.assertEqual(person["follower_count"], 0)
        self.assertNotIn("email", person)
        self.assertEqual(response.json()["next_page"], None)

    def test_follow_toggle_is_authenticated_and_cannot_target_self(self):
        toggle_url = reverse("social:toggle-follow", args=[self.jules.pk])
        self.assertEqual(self.client.post(toggle_url).status_code, 401)

        self.client.force_login(self.amelia)
        followed = self.client.post(toggle_url)
        unfollowed = self.client.post(toggle_url)

        self.assertEqual(followed.json(), {"following": True, "follower_count": 1})
        self.assertEqual(unfollowed.json(), {"following": False, "follower_count": 0})
        self.assertFalse(Follow.objects.exists())
        self.assertEqual(
            self.client.post(reverse("social:toggle-follow", args=[self.amelia.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse("social:toggle-follow", args=[99999])).status_code, 404
        )

    def test_follow_toggle_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.amelia)

        response = client.post(reverse("social:toggle-follow", args=[self.jules.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Follow.objects.exists())

    def test_feed_paginates_and_rejects_invalid_page_numbers(self):
        self.client.force_login(self.amelia)
        Post.objects.bulk_create(
            [Post(author=self.amelia, body=f"Moment {number}") for number in range(21)]
        )

        first = self.client.get(self.feed_url)
        second = self.client.get(self.feed_url, {"page": "2"})

        self.assertEqual(len(first.json()["results"]), 20)
        self.assertEqual(first.json()["next_page"], 2)
        self.assertEqual(len(second.json()["results"]), 1)
        self.assertIsNone(second.json()["next_page"])
        self.assertEqual(self.client.get(self.feed_url, {"page": "nope"}).status_code, 400)
        self.assertEqual(self.client.get(self.feed_url, {"page": "0"}).status_code, 400)

    def test_reaction_toggle_and_comments_use_the_session_user(self):
        post = Post.objects.create(author=self.amelia, body="A public thought")
        self.client.force_login(self.jules)
        reaction_url = reverse("social:toggle-reaction", args=[post.pk])
        comment_url = reverse("social:create-comment", args=[post.pk])

        liked = self.client.post(reaction_url)
        unliked = self.client.post(reaction_url)
        comment = self.client.post(comment_url, {"body": "That made me smile."})

        self.assertEqual(liked.json(), {"liked": True, "count": 1})
        self.assertEqual(unliked.json(), {"liked": False, "count": 0})
        self.assertEqual(comment.status_code, 201)
        saved_comment = Comment.objects.get()
        self.assertEqual(saved_comment.author, self.jules)
        self.assertEqual(saved_comment.post, post)
        self.assertEqual(comment.json()["comment"]["name"], self.jules.profile.display_name)

        self.client.force_login(self.amelia)
        feed_item = self.client.get(self.feed_url).json()["results"][0]
        self.assertEqual(feed_item["likes"], 0)
        self.assertEqual(feed_item["comment_count"], 1)
        self.assertEqual(feed_item["comments"][0]["text"], "That made me smile.")

    def test_private_posts_hide_all_actions_from_non_owners(self):
        post = Post.objects.create(
            author=self.amelia, body="Private note", visibility=Post.Visibility.PRIVATE
        )
        self.client.force_login(self.jules)

        reaction = self.client.post(reverse("social:toggle-reaction", args=[post.pk]))
        comment = self.client.post(
            reverse("social:create-comment", args=[post.pk]), {"body": "I can see this?"}
        )
        deletion = self.client.post(reverse("social:delete-post", args=[post.pk]))

        self.assertEqual(reaction.status_code, 404)
        self.assertEqual(comment.status_code, 404)
        self.assertEqual(deletion.status_code, 404)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())
        self.assertFalse(Comment.objects.exists())
        self.assertFalse(Reaction.objects.exists())

    def test_only_the_post_owner_can_delete_a_post(self):
        post = Post.objects.create(author=self.amelia, body="Keep this safe")
        self.client.force_login(self.jules)

        denied = self.client.post(reverse("social:delete-post", args=[post.pk]))

        self.assertEqual(denied.status_code, 404)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

        self.client.force_login(self.amelia)
        deleted = self.client.post(reverse("social:delete-post", args=[post.pk]))
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())

    def test_only_the_post_owner_can_edit_and_the_body_is_normalized(self):
        post = Post.objects.create(author=self.amelia, body="Original moment")
        edit_url = reverse("social:edit-post", args=[post.pk])

        self.client.force_login(self.jules)
        denied = self.client.post(edit_url, {"body": "Try to take over"})
        self.assertEqual(denied.status_code, 404)
        post.refresh_from_db()
        self.assertEqual(post.body, "Original moment")

        self.client.force_login(self.amelia)
        edited = self.client.post(edit_url, {"body": "  A better little moment  "})
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.json()["caption"], "A better little moment")
        self.assertTrue(edited.json()["can_edit"])
        self.assertTrue(edited.json()["edited"])
        post.refresh_from_db()
        self.assertEqual(post.body, "A better little moment")

        for body in (" ", "x" * 501):
            rejected = self.client.post(edit_url, {"body": body})
            self.assertEqual(rejected.status_code, 400)
        self.assertEqual(Post.objects.get(pk=post.pk).body, "A better little moment")

    def test_edit_api_requires_authentication_and_csrf(self):
        post = Post.objects.create(author=self.amelia, body="A small thought")
        edit_url = reverse("social:edit-post", args=[post.pk])

        self.assertEqual(self.client.post(edit_url, {"body": "Changed"}).status_code, 401)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.amelia)
        self.assertEqual(client.post(edit_url, {"body": "Changed"}).status_code, 403)
        post.refresh_from_db()
        self.assertEqual(post.body, "A small thought")

    def test_feed_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.amelia)

        response = client.post(self.create_url, {"body": "A CSRF protected moment"})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Post.objects.exists())
