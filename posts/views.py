from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html",
                  {"group": group, 'page': page, 'paginator': paginator})


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'paginator': paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    follow_status = None
    author = User.objects.get(username=username)
    posts = Post.objects.filter(author=author)
    total_posts = posts.count()
    followers = Follow.objects.filter(author=author.id).count()
    following = Follow.objects.filter(user=author.id).count()
    if request.user.username:
        follow_status = Follow.objects.filter(author=author.id, user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context_dict = {
        "posts": posts,
        'profile': author,
        'total_posts': total_posts,
        'followers': followers,
        'following': following,
        'page': page,
        'paginator': paginator,
        'follow_status': follow_status
    }
    return render(request, 'profile.html', context_dict)


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id)
    total_posts = Post.objects.filter(author=author).count()
    form = CommentForm()
    items = Comment.objects.filter(post=post).order_by("created")
    context_dict = {
        "post": post,
        "username": username,
        "author": author,
        "total_posts": total_posts,
        "form": form,
        "items": items
    }
    return render(request, "post.html", context_dict)



@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect("post", username=request.user.username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("post", username=request.user.username, post_id=post_id)
    return render(request, "new.html", {"form": form, "post": post})


@login_required
def post_delete(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    if request.user != profile:
        return redirect("post", username=request.user.username, post_id=post_id)
    Post.objects.filter(id=post_id).delete()
    return redirect("profile", username=request.user.username)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author = request.user
            new_comment.post = post
            new_comment.save()
    return redirect('post', username, post_id)


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user).values('author')
    posts = Post.objects.select_related('author').filter(author__in=follow)
    posts_list = [post for post in posts]
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {
        'page': page,
        'paginator': paginator,
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    already_followed = Follow.objects.filter(user=request.user.id, author=author.id).exists()
    if author.id != request.user.id and not already_followed: Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    already_followed = Follow.objects.filter(user=request.user.id, author=author.id).exists()
    if already_followed:
        Follow.objects.filter(user=request.user.id, author=author.id).delete()
    return redirect('profile', username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
