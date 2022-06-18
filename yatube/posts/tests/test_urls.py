from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём экземпляр user, group, post, comment, follow"""
        super().setUpClass()
        cls.user_author = User.objects.create(username='Im_author')
        cls.user_not_author = User.objects.create(username='Im_not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_not_author,
            text='Тест-комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.user_not_author,
            author=cls.user_author
        )

    def setUp(self) -> None:
        self.guest_client = Client()

        self.author_client = Client()
        self.author_client.force_login(self.user_author)

        self.not_author_client = Client()
        self.not_author_client.force_login(self.user_not_author)
        cache.clear()

    def test_urls_response(self):
        """Есть ответ по всем url. С авторизацией, если есть требование."""
        urls = [  # (url, auth_require flag)
            (reverse('posts:index'), False),
            (reverse('posts:group_list', kwargs={'slug': self.group.slug}),
             False),
            (reverse('posts:profile', kwargs={'username': self.user_author}),
             False),
            (reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
             False),
            (reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
             True),
            (reverse('posts:post_create'), True),
            (reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
             True),
            (reverse('posts:follow_index'), True),
            (reverse('posts:profile_follow',
                     kwargs={'username': self.user_author}),
             True),
            (reverse('posts:profile_unfollow',
                     kwargs={'username': self.user_author}),
             True),
        ]
        # delete url must be last:
        urls += [(reverse('posts:post_delete',
                          kwargs={'post_id': self.post.pk}), True)]
        for url, auth_requiring in urls:
            with self.subTest(url=url):
                client = (self.author_client if auth_requiring
                          else self.guest_client)
                response = client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 f'[!] Нет ответа по адресу {url}!')

    def test_redirect_auth_required_urls(self):
        """Проверка переадресации на страницах, требующих авторизации."""
        redirect_url_param = '/auth/login/?next='
        urls = [
            f'/posts/{self.post.pk}/edit/',
            '/create/',
            f'/posts/{self.post.pk}/delete/',
            f'/posts/{self.post.pk}/comment/',
            '/follow/',
            f'/profile/{self.user_author}/follow/',
            f'/profile/{self.user_author}/unfollow/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url_param + url)

    def test_redirect_author_required_urls(self):
        """Проверка переадресации, требующих авторства."""
        urls_trace = {
            f'/posts/{self.post.pk}/edit/': f'/posts/{self.post.pk}/',
            f'/posts/{self.post.pk}/delete/': f'/posts/{self.post.pk}/',
        }
        for url, redirect_url in urls_trace.items():
            with self.subTest(url=url):
                response = self.not_author_client.get(url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_urls_uses_correct_template(self):
        """Тест, что URL-адрес использует соответствующий шаблон."""
        url_templates = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user_author}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
            f'/profile/{self.user_author}/follow/': 'posts/profile.html',
            f'/profile/{self.user_author}/unfollow/': 'posts/profile.html',
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.author_client.get(url, follow=True)
                self.assertTemplateUsed(
                    response, template,
                    (f'Страница по адресу {url} должна использовать '
                     f'шаблон {template}!')
                )

    def test_unexisting_url(self):
        """Запрос на несуществующий в проекте URL."""
        url = '/unexisting_url/'
        response = self.not_author_client.get(url)
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND,
            'По несуществующему адресу код ответа должен быть 404!')
