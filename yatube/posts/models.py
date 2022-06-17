from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """Модель группы публикаций."""
    title = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Введите название группы'
    )
    slug = models.SlugField(
        'Семантический URL',
        unique=True,
        help_text='Короткий тэг для группы'
    )
    description = models.TextField(
        'Описание',
        help_text='Введите описание группы.'
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'


class Post(models.Model):
    """Модель публикации."""
    text = models.TextField(
        'Текст публикации',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикации'
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    """Модель комментария к публикации."""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Комментируемая публикация',
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        related_name='comments'
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Что вы думаете по этому поводу?'
    )
    created = models.DateTimeField(
        'Время публикации комментария',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created']

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
