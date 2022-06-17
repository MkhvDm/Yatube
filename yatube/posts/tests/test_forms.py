import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='Im_author')
        cls.group_test = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.author_client = Client()
        self.author_client.force_login(PostFormTests.user_author)

        self.post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        self.form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTests.group_test.id,
            'image': uploaded,
        }
        self.response = self.author_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )

    def test_form_post_create(self):
        """Новая запись успешно создаётся через форму."""
        self.assertRedirects(self.response, reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.user_author.username}))
        self.assertEqual(Post.objects.count(), self.post_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Тестовый текст',
            author=PostFormTests.user_author,
            group=PostFormTests.group_test,
            image='posts/small.gif'
        ).exists())

    def test_form_post_edit(self):
        """Пост успешно редактируется через форму."""
        # change pic:
        small_gif_upd = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3A'
        )
        uploaded_upd = SimpleUploadedFile(
            name='small_upd.gif',
            content=small_gif_upd,
            content_type='image/gif',
        )
        edit_form_data = {
            'text': 'Обновлённый текст',
            'group': '',  # crutch? equal None
            'image': uploaded_upd,
        }
        edit_response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=edit_form_data,
            follow=True
        )
        self.assertRedirects(edit_response, reverse(
            'posts:post_detail', kwargs={'post_id': 1}
        ))
        self.assertTrue(Post.objects.filter(
            text='Обновлённый текст',
            author=PostFormTests.user_author,
            group=None,
            image='posts/small_upd.gif'
        ).exists())


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='Im_author')
        cls.user_commentator = User.objects.create(username='Im_commentator')

    def setUp(self) -> None:
        self.author_client = Client()
        self.author_client.force_login(CommentFormTest.user_author)

        self.commentator_client = Client()
        self.commentator_client.force_login(CommentFormTest.user_commentator)

        self.test_post = Post.objects.create(
            author=CommentFormTest.user_author,
            text='Пост для коммента'
        )

    def test_add_comment(self):
        """Успешное создание комментария через форму."""
        comment_count = Comment.objects.count()  # 0
        form_comment = {
            'text': 'Текст комментария'
        }
        response = self.commentator_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.test_post.id}),
            data=form_comment,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.test_post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            post=self.test_post.id,
            text='Текст комментария',
            author=CommentFormTest.user_commentator
        ).exists())
