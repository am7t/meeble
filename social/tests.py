from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from accounts.models import Profile
from .models import Comment, Follow, Post, Reaction


class SocialSchemaTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.amelia = User.objects.create_user("amelia@example.com", "safe demo password")
        self.jules = User.objects.create_user("jules@example.com", "safe demo password")
        Profile.objects.create(user=self.amelia, handle="amelia", display_name="Amelia Rose")
        Profile.objects.create(user=self.jules, handle="jules", display_name="Jules Parker")
        self.post = Post.objects.create(author=self.amelia, body="A small happy moment")

    def test_sqlite_enforces_foreign_keys(self):
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys")
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_profile_handles_are_case_insensitively_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.create(user=self.create_user("third@example.com"), handle="AMELIA")

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
            Profile.objects.create(
                user=self.create_user("third@example.com"), handle="a", display_name="A"
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.create(
                user=self.create_user("fourth@example.com"), handle="fourth", display_name="d" * 41
            )

    def test_deleting_an_account_cascades_its_social_records(self):
        self.amelia.delete()
        self.assertFalse(Profile.objects.filter(handle="amelia").exists())
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    @staticmethod
    def create_user(email):
        return get_user_model().objects.create_user(email, "safe demo password")
