from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect,\
    HttpResponseForbidden, HttpResponseNotAllowed, JsonResponse
from django.views.generic import View
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import IntegrityError
from django.db.models import Q
from django.utils.http import urlencode
from django.contrib import messages
from .models import Post, Category
from .forms import NewPostForm


class PostsListView(View):
    filters = {
        'approved': Q(status=Post.APPROVED),
        'hidden': Q(status=Post.HIDDEN),
        'all': Q(status=Post.ALL) | Q(status=Post.APPROVED)
    }

    def get_queryset(self, *args, **kwargs):
        return Post.objects.select_related('category').filter(self.filters[kwargs['posts_type']])

    def get(self, request, *args, **kwargs):
        pgtr = Paginator(self.get_queryset(*args, **kwargs).order_by('-pinned', '-pub_date'), 10)
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


def index(request):
    return redirect(reverse('onechan:approved_posts'), permanent=True)


def show_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'onechan/post.html', {'post': post})


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
            return redirect(reverse('onechan:show_post', kwargs={'post_id': post.id}))
        else:
            return render(request, 'onechan/add_post.html', status=400, context={
                'form': form
                })
