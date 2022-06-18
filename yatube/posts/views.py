from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(settings.INDEX_CACHE_TIMEOUT_SEC, key_prefix='index_page')
def index(request):
    """Возвращает http-ответ с N последними публикациями."""
    paginated_posts = Paginator(
        Post.objects
        .select_related('author', 'group'),
        settings.NUM_OF_POSTS_ON_PAGE
    )
    page_obj = paginated_posts.get_page(request.GET.get('page'))
    return render(request, 'posts/index.html',
                  {'title': 'Добро пожаловать в yaTube',
                   'page_obj': page_obj})


def profile(request, username):
    """Профиль пользователя с его публикациями."""
    author = User.objects.get(username=username)
    paginated_posts = Paginator(
        author.posts.select_related('group').all(),
        settings.NUM_OF_POSTS_ON_PAGE
    )
    page_obj = paginated_posts.get_page(request.GET.get('page'))
    if request.user.is_anonymous:
        following = False
    else:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Подробная информация о публикации."""
    post_query = (
        Post.objects
        .filter(id=post_id)
        .select_related('group', 'author')
    )
    post = get_object_or_404(post_query)
    num_posts = Post.objects.filter(author_id=post.author_id).count()
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'num_posts': num_posts,
        'comments': comments,
        'comment_form': CommentForm()
    }
    return render(request, 'posts/post_detail.html', context)


def group_posts(request, slug):
    """
    Возвращает http-ответ с N последними публикациями определённой группы.
    """
    group = get_object_or_404(Group, slug=slug)
    paginated_posts = Paginator(
        group.posts.select_related('author'),
        settings.NUM_OF_POSTS_ON_PAGE
    )
    page_obj = paginated_posts.get_page(request.GET.get('page'))
    return render(request, 'posts/group_list.html',
                  {'group': group,
                   'page_obj': page_obj,
                   'group_page': True})


@login_required
def post_create(request):
    """Функция обеспечивает создания публикации."""
    form = PostForm(data=request.POST or None, files=request.FILES or None)
    if request.method == 'GET' or not form.is_valid():
        return render(request, 'posts/create_post.html',
                      {'form': form,
                       'is_edit': False})
    post_inst = form.save(commit=False)
    post_inst.author = request.user
    post_inst.save()
    return redirect('posts:profile', username=request.user.username)


@login_required
def post_edit(request, post_id):
    """Функция обеспечивает редактирование публикации."""
    post = get_object_or_404(Post, pk=post_id)
    if request.user.id != post.author_id:
        return redirect('posts:post_detail', post_id=post_id)
    if request.method == 'POST':
        form = PostForm(instance=post,
                        data=request.POST,
                        files=request.FILES)
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/create_post.html',
                  {'post_id': post_id,
                   'form': form,
                   'is_edit': True})


@login_required
def post_delete(request, post_id):
    """Удаление публикации."""
    post = get_object_or_404(Post, pk=post_id)
    if request.user.id != post.author_id:
        return redirect('posts:post_detail', post_id=post_id)
    post.delete()
    return redirect('posts:index')


@login_required
def add_comment(request, post_id):
    """Функция добавления комментария к публикации."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    my_subscriptions = Follow.objects.filter(user=request.user.id)
    follow_posts = (Post.objects
                    .filter(author__in=my_subscriptions.values('author'))
                    .select_related('author', 'group')
                    )
    paginated_posts = Paginator(
        follow_posts,
        settings.NUM_OF_POSTS_ON_PAGE
    )
    page_obj = paginated_posts.get_page(request.GET.get('page'))
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    if request.user.username != username:
        Follow.objects.get_or_create(
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора."""
    if request.user.username != username:
        following = get_object_or_404(
            Follow,
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
        following.delete()
    return redirect('posts:profile', username=username)
