from http import HTTPStatus
from time import sleep

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.db.models.query import QuerySet
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.num_of_authors = 2
        cls.user_author = User.objects.create(username='Im_author')
        cls.user_author_too = User.objects.create(username='Im_author_too')
        cls.authors = [cls.user_author, cls.user_author_too]

        cls.num_of_test_groups = 2
        cls.groups = []
        for i in range(cls.num_of_test_groups):
            cls.groups.append(
                Group.objects.create(
                    title=f'Тестовая группа {i}',
                    slug=f'test-group-slug-{i}',
                    description=f'Тестовое описание {i}',
                )
            )

        cls.num_of_test_posts = 22  # required 22+, recommended not x10
        cls.posts = []
        for i in range(cls.num_of_test_posts):
            cls.posts.append(Post.objects.create(
                author=cls.authors[i % cls.num_of_test_groups],
                text=f'Тестовый пост {i}',
                group=cls.groups[i % cls.num_of_test_groups]
            ))
            sleep(0.001)  # for different pub_date

        # image preparing:
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        # add pic only for last post:
        (Post.objects.filter(pk=cls.num_of_test_posts)
                     .update(image=cls.uploaded))

    def setUp(self) -> None:
        self.guest_client = Client()

        self.author_client = Client()
        self.author_client.force_login(PostViewsTests.user_author)

        self.author_too_client = Client()
        self.author_too_client.force_login(PostViewsTests.user_author_too)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_page_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-group-slug-0'}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': PostViewsTests.user_author}):
                'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}):
                'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}):
                'posts/create_post.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:follow_index'):
                'posts/follow.html',
            reverse('posts:profile_follow',
                    kwargs={'username': 'Im_author_too'}):
                'posts/profile.html',
            reverse('posts:profile_unfollow',
                    kwargs={'username': 'Im_author_too'}):
                'posts/profile.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name, follow=True)
                self.assertTemplateUsed(response, template)

    # index testing:
    def test_index_context_types(self):
        """В контекст index'а передаются объекты верных типов."""
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        expected_types = {
            'title': str,
            'page_obj': Page,
            'group_link_is_visible': bool
        }
        for context_key, context_type in expected_types.items():
            with self.subTest(context_key=context_key):
                self.assertIsInstance(
                    response.context[context_key],
                    context_type)

    def test_index_page_1_context(self):
        """Число постов на 1 странице index равно N (default: 10)."""
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']),
            settings.NUM_OF_POSTS_ON_PAGE)

    def test_index_last_page_context(self):
        """На последней странице index верное число постов %N."""
        n_posts = PostViewsTests.num_of_test_posts
        posts_on_page = settings.NUM_OF_POSTS_ON_PAGE
        last_page_num = (n_posts + (posts_on_page - 1)) // posts_on_page
        expected_last_page_posts_num = (
            posts_on_page
            if not (n_posts % posts_on_page)
            else n_posts % posts_on_page
        )
        response = self.guest_client.get(
            reverse('posts:index') + f'?page={last_page_num}')
        self.assertEqual(
            len(response.context['page_obj']),
            expected_last_page_posts_num)

    # group_list testing:
    def test_group_context_types(self):
        """В контекст group_list'а передаются объекты верных типов."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug-0'})
        )
        expected_types = {
            'group': Group,
            'page_obj': Page,
            'group_link_is_visible': bool
        }
        for context_key, context_type in expected_types.items():
            with self.subTest(context_key=context_key):
                self.assertIsInstance(
                    response.context[context_key],
                    context_type)

    def test_correct_group_selecting(self):
        """На странице group_list посты только определённой группы."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug-0'})
        )
        for post in response.context['page_obj']:
            with self.subTest(post=post):
                self.assertEqual(post.group.slug, 'test-group-slug-0')

    def test_group_page_1_context(self):
        """Число постов на 1 странице group_list равно N (default: 10)."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug-0'})
        )
        self.assertEqual(
            len(response.context['page_obj']),
            settings.NUM_OF_POSTS_ON_PAGE
        )

    def test_group_last_page_context(self):
        """На последней странице group_list верное число постов."""
        group_id = 0
        n_posts = PostViewsTests.num_of_test_posts
        n_groups = PostViewsTests.num_of_test_groups
        posts_on_page = settings.NUM_OF_POSTS_ON_PAGE

        n_group_posts = (n_posts + (n_groups - 1)) // n_groups
        last_page_num = (n_group_posts + (posts_on_page - 1)) // posts_on_page
        expected_last_page_posts_num = (
            posts_on_page
            if not (n_group_posts % posts_on_page)
            else n_group_posts % posts_on_page
        )
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'test-group-slug-{group_id}'}
            ) + f'?page={last_page_num}')

        self.assertEqual(
            len(response.context['page_obj']),
            expected_last_page_posts_num)

    def test_unexist_group_slug(self):
        """Переадресация при запросе group_list несуществующей группы."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'unexist-slug'}),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # profile testing:
    def test_profile_context_types(self):
        """В контекст profile'а передаются объекты верных типов."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'Im_author'})
        )
        expected_types = {
            'page_obj': Page,
            'author': User,
            'following': bool,
            'group_link_is_visible': bool
        }
        for context_key, context_type in expected_types.items():
            with self.subTest(context_key=context_key):
                self.assertIsInstance(
                    response.context[context_key],
                    context_type)

    def test_correct_profile_selecting(self):
        """На странице profile посты только определённого автора."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'Im_author'})
        )
        for post in response.context['page_obj']:
            with self.subTest(post=post):
                self.assertEqual(post.author.username, 'Im_author')

    def test_profile_page_1_context(self):
        """Число постов на 1 странице profile равно N (default: 10)."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'Im_author'})
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.NUM_OF_POSTS_ON_PAGE
                         )

    def test_profile_last_page_context(self):
        """На последней странице profile верное число постов."""
        n_posts = PostViewsTests.num_of_test_posts
        posts_on_page = settings.NUM_OF_POSTS_ON_PAGE
        n_author_posts = (n_posts // 2) + 1 if n_posts % 2 else n_posts // 2
        last_page_num = (n_author_posts + (posts_on_page - 1)) // posts_on_page
        expected_last_page_posts_num = (
            posts_on_page
            if not (n_author_posts % posts_on_page)
            else n_author_posts % posts_on_page
        )
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'Im_author'})
            + f'?page={last_page_num}')
        self.assertEqual(
            len(response.context['page_obj']),
            expected_last_page_posts_num)

    # post_detail & commenting testing:
    def test_post_detail_context_types(self):
        """В контекст post_detail'а передаются объекты верных типов."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        expected_types = {'post': Post,
                          'num_posts': int,
                          'comments': QuerySet,
                          'comment_form': CommentForm
                          }
        for context_key, context_type in expected_types.items():
            with self.subTest(context_key=context_key):
                self.assertIsInstance(
                    response.context[context_key],
                    context_type)

    def test_correct_post_detail_selecting(self):
        """На странице post_detail верный пост."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        expected_post = {
            'id': 1,
            'author': 1,  # author_id
            'group': 1,
            'text': 'Тестовый пост 0'
        }
        for field, value in expected_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    response.context['post'].serializable_value(field),
                    value)

    def test_correct_num_of_authors_posts(self):
        """На странице post_detail выводится верное число постов автора."""
        # for author = 'Im_author'
        n_posts = PostViewsTests.num_of_test_posts
        n_author_posts = (n_posts // 2) + 1 if n_posts % 2 else n_posts // 2
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertEqual(response.context.get('num_posts'), n_author_posts)

    def test_add_comment_no_auth(self):
        """Переадресация на login при попытке комментировать."""
        comment_url = reverse('posts:add_comment', kwargs={'post_id': 1})
        response = self.guest_client.get(comment_url)
        self.assertRedirects(response,
                             reverse('users:login') + f'?next={comment_url}')

    def test_add_comment(self):
        """На странице поста верный комментарий."""
        post_id = 1
        comment = Comment.objects.create(
            post=PostViewsTests.posts[post_id - 1],
            author=PostViewsTests.user_author_too,
            text='Текст комментария'
        )
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        self.assertEqual(response.context['comments'][0], comment)

    def test_unexisting_post(self):
        """На запрос несуществующего поста возвращается ошибка 404."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 666}),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # post_edit testing:
    def test_post_edit_context_types(self):
        """В контекст post_edit передаются объекты верных типов."""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        expected_types = {
            'post_id': int,
            'form': PostForm,
            'is_edit': bool
        }
        for context_key, context_type in expected_types.items():
            with self.subTest(context_key=context_key):
                self.assertIsInstance(
                    response.context[context_key],
                    context_type)

    def test_post_edit_form(self):
        """Проверка полей формы редактирования поста."""
        response_form = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        ).context.get('form')
        form_fields = {
            'text': (forms.fields.CharField, 'Тестовый пост 0'),
            'group': (forms.models.ModelChoiceField, 1),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response_form.fields[value]
                field_pre_value = response_form[value].value()
                self.assertIsInstance(form_field, expected[0])
                self.assertEqual(field_pre_value, expected[1])

    def test_post_edit_redirect(self):
        """Не автор поста перенаправляется на страницу поста."""
        response = self.author_too_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1}), follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': 1}))

    # post_create testing:
    def test_post_create_context_types(self):
        """В контекст post_create передаются объекты верных типов."""
        response = self.author_client.get(reverse('posts:post_create'))
        expected_types = {
            'form': PostForm,
            'is_edit': bool
        }
        for context_key, context_type in expected_types.items():
            with self.subTest(context_key=context_key):
                self.assertIsInstance(response.context[context_key],
                                      context_type)

    def test_post_create_correct_on_paginated_pages(self):
        """При создании поста он появляется на главной, в группе, в профиле."""
        cache.clear()
        new_post = Post.objects.create(
            author=PostViewsTests.user_author,
            text='Пост с группой 0',
            group=PostViewsTests.groups[0]
        )
        urls_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug-0'}),
            reverse('posts:profile', kwargs={'username': 'Im_author'})
        )
        for url in urls_names:
            with self.subTest(url=url):
                created_post = (self.author_client.get(url)
                                .context['page_obj'][0])
                self.assertEqual(created_post, new_post)

        last_post_in_other_group = self.author_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test-group-slug-1'}
                    )).context['page_obj'][0]
        self.assertNotEqual(last_post_in_other_group, new_post,
                            'Пост не должен появиться на странице этой группы!'
                            )

    # post_delete testing:
    def test_post_delete_not_author_redirect(self):
        """Не автор поста перенаправляется на страницу поста."""
        response = self.author_too_client.get(
            reverse('posts:post_delete', kwargs={'post_id': 1}), follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': 1}))

    def test_unexist_post_delete_redirect(self):
        """При удалении несуществующего поста возвращается ошибка 404."""
        response = self.author_client.get(
            reverse('posts:post_delete', kwargs={'post_id': 666}), follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_correct_deleting(self):
        """Проверка корректного удаления поста."""
        num_of_posts_before = Post.objects.count()
        Post.objects.create(
            author=PostViewsTests.authors[0],
            text='Тестовый пост для удаления'
        )
        post = Post.objects.filter(text='Тестовый пост для удаления').get()
        response = self.author_client.get(
            reverse('posts:post_delete', kwargs={'post_id': post.id}),
            follow=True)
        self.assertRedirects(response, reverse('posts:index'))
        num_of_posts_after = Post.objects.count()
        self.assertEqual(num_of_posts_before, num_of_posts_after)

    # PIC tests:
    def test_pic_in_all_views(self):
        """Картинка верно передаётся по всем адресам."""
        cache.clear()
        last_post = Post.objects.get(id=PostViewsTests.num_of_test_posts)
        urls_context_obj = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:profile',
                    kwargs={'username': last_post.author}): 'page_obj',
            reverse('posts:group_list',
                    kwargs={'slug': last_post.group.slug}): 'page_obj',
            reverse('posts:post_detail',
                    kwargs={'post_id': last_post.id}): 'post',
        }
        for url, context_key in urls_context_obj.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                post_or_posts = response.context[context_key]
                if isinstance(post_or_posts, Post):
                    context_image = post_or_posts.image
                else:
                    context_image = post_or_posts[0].image
                self.assertEqual(context_image, PostViewsTests.uploaded)

    # cache testing:
    def test_cache(self):
        """Загрузка из кэша доступна в течение заданого времени."""
        cache.clear()
        Post.objects.create(
            author=PostViewsTests.authors[0],
            text='Тестовый пост для кэширования'
        )
        response_fill_cache = self.guest_client.get(reverse('posts:index'))
        Post.objects.filter(text='Тестовый пост для кэширования').delete()
        response_cache = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response_fill_cache.content, response_cache.content)
        cache.clear()
        response_no_cache = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response_fill_cache.content,
                            response_no_cache.content)

    # followings testing:
    def test_follow_index_context_types(self):
        """В контекст follow_index передаются объекты верных типов."""
        response = self.author_client.get(reverse('posts:follow_index'))
        expected_types = {
            'page_obj': Page,
            'group_link_is_visible': bool
        }
        for context_key, context_type in expected_types.items():
            with self.subTest(context_key=context_key):
                self.assertIsInstance(response.context[context_key],
                                      context_type)

    def test_follow_n_unfollow(self):
        """Пользователь может подписаться на автора и отписаться."""
        author = 'Im_author_too'
        resp_follow = self.author_client.get(
            reverse('posts:profile_follow', kwargs={'username': author})
        )
        self.assertRedirects(
            resp_follow, reverse('posts:profile', kwargs={'username': author})
        )
        self.assertTrue(
            Follow.objects.filter(
                user=PostViewsTests.authors[0],
                author=PostViewsTests.authors[1]
            ).exists()
        )
        resp_unfollow = self.author_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': author})
        )
        self.assertRedirects(
            resp_unfollow,
            reverse('posts:profile', kwargs={'username': author})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=PostViewsTests.authors[0],
                author=PostViewsTests.authors[1]
            ).exists()
        )

    def test_correct_select_posts_by_following(self):
        """Записи автора отображаются в Избранном только у подписчиков."""
        test_user = User.objects.create(username='Im_tester')
        self.tester_client = Client()
        self.tester_client.force_login(test_user)
        Follow.objects.create(
            user=test_user, author=PostViewsTests.authors[0]
        )
        follow_resp = self.tester_client.get(reverse('posts:follow_index'))
        for post in follow_resp.context['page_obj']:
            with self.subTest(post=post):
                self.assertEqual(post.author.username, 'Im_author')

        non_follow_resp = self.author_too_client.get(
            reverse('posts:follow_index')
        )
        for post in non_follow_resp.context['page_obj']:
            with self.subTest(post=post):
                self.assertNotEqual(post.author.username, 'Im_author')
