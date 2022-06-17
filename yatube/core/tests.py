from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class CoreViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='Im_author')

    def setUp(self) -> None:
        self.guest_client = Client()

    def test_custom_error_templates(self):
        """Используются кастомные шаблоны ошибок."""
        url_template_cases = (
            ('/unexist/', self.guest_client, 'core/404.html'),
        )
        for url, client, template in url_template_cases:
            with self.subTest(url=url):
                response = client.get(url, follow=True)
                self.assertTemplateUsed(response, template)
