from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём экземпляр user, group & post."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='tester')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост. Длина более 15 символов.',
        )

    def test_post_have_correct_objects_name(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        expected_obj_name = PostModelTest.post.text[:15]
        self.assertEqual(
            expected_obj_name,
            PostModelTest.post.__str__(),
            '[!] Метод __str__ у модели Post работает неверно!'
        )

    def test_post_verbose_names(self):
        """Проверяем, что у полей модели Post верные verbose_name."""
        field_verboses = {
            'text': 'Текст публикации',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_verbose_name in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).verbose_name,
                    expected_verbose_name,
                    '[x] Значение verbose_name не соответствует ожидаемому.'
                )

    def test_post_help_text(self):
        """Проверяем, что у полей модели Post верные help_text."""
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_help_text in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).help_text,
                    expected_help_text,
                    '[x] Значение help_text не соответствует ожидаемому.'
                )


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём экземпляр user, group & post."""
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group-slug',
            description='Тестовое описание',
        )

    def test_group_have_correct_objects_name(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        expected_obj_name = GroupModelTest.group.title
        self.assertEqual(
            expected_obj_name,
            str(GroupModelTest.group),
            '[!] Метод __str__ у модели Group работает неверно!'
        )

    def test_group_verbose_names(self):
        """Проверяем, что у полей модели Group верные verbose_name."""
        field_verboses = {
            'title': 'Название',
            'slug': 'Семантический URL',
            'description': 'Описание'
        }
        for field, expected_verbose_name in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    GroupModelTest.group._meta.get_field(field).verbose_name,
                    expected_verbose_name,
                    '[x] Значение verbose_name не соответствует ожидаемому.'
                )

    def test_group_help_text(self):
        """Проверяем, что у полей модели Group верные help_text."""
        field_help_text = {
            'title': 'Введите название группы',
            'slug': 'Короткий тэг для группы',
            'description': 'Введите описание группы.'
        }
        for field, expected_help_text in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    GroupModelTest.group._meta.get_field(field).help_text,
                    expected_help_text,
                    '[x] Значение help_text не соответствует ожидаемому.'
                )


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='comment_tester')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для комментирования.',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Текст комментария'
        )

    def test_comment_have_correct_objects_name(self):
        """Проверяем, что у модели Comment корректно работает __str__."""
        expected_obj_name = CommentModelTest.comment.text[:15]
        self.assertEqual(
            expected_obj_name,
            str(CommentModelTest.comment),
            '[!] Метод __str__ у модели Comment работает неверно!'
        )

    def test_comment_verbose_names(self):
        """Проверяем, что у полей модели Comment верные verbose_name."""
        field_verboses = {
            'post': 'Комментируемая публикация',
            'author': 'Автор комментария',
            'text': 'Текст комментария',
            'created': 'Время публикации комментария'
        }
        for field, expected_verbose_name in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    (CommentModelTest.comment._meta.get_field(field)
                     .verbose_name),
                    expected_verbose_name,
                    '[x] Значение verbose_name не соответствует ожидаемому.'
                )

    def test_group_help_text(self):
        """Проверяем, что у полей модели Group верные help_text."""
        field_help_text = {
            'text': 'Что вы думаете по этому поводу?',
        }
        for field, expected_help_text in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    CommentModelTest.comment._meta.get_field(field).help_text,
                    expected_help_text,
                    '[x] Значение help_text не соответствует ожидаемому.'
                )


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём экземпляр user1, user2, follow"""
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='tester1')
        cls.user2 = User.objects.create_user(username='tester2')
        cls.follow = Follow.objects.create(
            user=cls.user1,
            author=cls.user2
        )

    def test_follow_have_correct_objects_name(self):
        """Проверяем, что у модели Comment корректно работает __str__."""
        expected_obj_name = (f'{FollowModelTest.user1} подписан на '
                             f'{FollowModelTest.user2}')
        self.assertEqual(
            expected_obj_name,
            str(FollowModelTest.follow),
            '[!] Метод __str__ у модели Follow работает неверно!'
        )

    def test_comment_verbose_names(self):
        """Проверяем, что у полей модели Follow верные verbose_name."""
        field_verboses = {
            'user': 'Подписчик',
            'author': 'Автор',
        }
        for field, expected_verbose_name in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    (FollowModelTest.follow._meta.get_field(field)
                     .verbose_name),
                    expected_verbose_name,
                    '[x] Значение verbose_name не соответствует ожидаемому.'
                )
