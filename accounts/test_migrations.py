from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ExistingAccountProfileMigrationTests(TransactionTestCase):
    migrate_from = [("accounts", "0001_initial"), ("social", None)]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state([("accounts", "0001_initial")]).apps
        HistoricalUser = old_apps.get_model("accounts", "User")
        self.user = HistoricalUser.objects.create(email="legacy.member@example.com", password="!")

        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        current_apps = executor.loader.project_state(executor.loader.graph.leaf_nodes()).apps
        Profile = current_apps.get_model("accounts", "Profile")
        self.profile = Profile.objects.get(user_id=self.user.pk)

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_account_receives_a_stable_profile(self):
        self.assertEqual(self.profile.handle, f"m_{self.user.pk}")
        self.assertEqual(self.profile.display_name, "Legacy Member")
