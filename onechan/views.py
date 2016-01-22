from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect,\
    HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from django.views.generic import View
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import IntegrityError
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.http import urlencode
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from .models import Post, Category, Comment, Favourite
from .forms import NewPostForm, NewCommentForm
from .utils import notify
from .utils.stats import update_posting_stats


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PostsListView(View):
    filters = {
        'approved': Q(status=Post.APPROVED),
        'hidden': Q(status=Post.HIDDEN),
        'all': Q(status=Post.ALL) | Q(status=Post.APPROVED)
    }

    def get_queryset(self, request, *args, **kwargs):
        return Post.objects.select_related('category').filter(self.filters[kwargs['posts_type']])

    def get(self, request, *args, **kwargs):
        pgtr = Paginator(self.get_queryset(request, *args, **kwargs).order_by('-pinned', '-pub_date'), 10)
        page = request.GET.get("page")
        try:
            posts = pgtr.page(page)
        except PageNotAnInteger:
            posts = pgtr.page(1)
        except EmptyPage:
            return HttpResponseRedirect(request.path +
                '?' + urlencode({'page': pgtr.num_pages}))
        return render(request, "onechan/posts_list.html", {
            'posts': posts,
        })


@method_decorator(ensure_csrf_cookie, name='dispatch')
class FavouritesListView(PostsListView):

    def get_queryset(self, request, *args, **kwargs):
        return Post.objects.filter(favourite__user_ip=request.META['REMOTE_ADDR'])


def index(request):
    return redirect(reverse('onechan:approved_posts'), permanent=True)


def show_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.add_viewer(request.META['REMOTE_ADDR'])
    return render(request, 'onechan/post.html', {'post': post, 'comment_form': NewCommentForm()})


def add_post(request):
    if request.method == 'GET':
        return render(request, 'onechan/add_post.html', {'form': NewPostForm()})
    elif request.method == 'POST':
        post = Post(author_ip=request.META['REMOTE_ADDR'])
        form = NewPostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            cat_key = form.cleaned_data['category']
            if cat_key:
                post.category = Category.objects.get(key=cat_key)
            post.save()
            post_url = reverse('onechan:show_post', kwargs={'post_id': post.id})
            notify({
                'type': 'new_post',
                'data': {
                    'title': post.title,
                    'url' : post_url
                }
            })
            update_posting_stats()
            return redirect(post_url)
        else:
            return render(request, 'onechan/add_post.html', status=400, context={
                'form': form
                })

def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        if post.closed:
            return HttpResponseForbidden()
        comment = Comment(author_ip=request.META['REMOTE_ADDR'], post=post)
        form = NewCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            if post.bumpable:
                post.bump_date = timezone.now()
            post.save()
            notify({
                'type': 'new_comment',
                'room': 'news_' + post_id,
                'data': {
                    'id': comment.id,
                    'post_id': post_id,
                    'html': render_to_string(
                        'onechan/comment_partial.html',
                        context={'comment': comment},
                        request=request
                    )
                }
            })
            update_posting_stats()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        return HttpResponseNotAllowed(['POST'])

def rate_post(request, post_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    post = get_object_or_404(Post, pk=post_id)
    ip = request.META['REMOTE_ADDR']
    value = 1 if int(request.POST.get('value', -1)) == 1 else -1
    if post.rate(ip, value):
        notify({
            'type': 'new_rating',
            'data': {
                'post_id': post_id,
                'rating': post.rating
            }
        })
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'had_voted'}, status=403)

def set_favourite(request, post_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    post = get_object_or_404(Post, pk=post_id)
    ip = request.META['REMOTE_ADDR']
    value = request.POST.get('value') in ['1', 'true']
    post.set_favourite(ip, value)
    return JsonResponse({
        'success': True,
        'favourite': value,
        'post_id': post.id
    })
