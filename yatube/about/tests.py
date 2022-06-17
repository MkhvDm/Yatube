from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_pages_exist(self):
        """Тест общедоступных страниц, а также соответствия HTML-шаблонов."""
        url_template_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template_name in url_template_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 f'[!] Нет ответа по адресу {url}!')
                self.assertTemplateUsed(
                    response, template_name,
                    (f'Страница по адресу {url} должна использовать '
                     f'шаблон {template_name}!')
                )
