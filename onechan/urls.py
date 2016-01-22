from django.conf.urls import url
from . import views
# Create your views here.

urlpatterns = [
    url(r'^$', views.index),
    url(r"^news$", views.PostsListView.as_view(), {'posts_type': 'approved'}, name='approved_posts'),
    url(r"^news/all$", views.PostsListView.as_view(), {'posts_type': 'all'}, name='all_posts'),
    url(r"^news/hidden$", views.PostsListView.as_view(), {'posts_type': 'hidden'}, name='hidden_posts'),

    url(r'^news/(?P<post_id>[0-9]+)$', views.show_post, name='show_post'),
    url(r'^news/add$', views.add_post, name='add_post'),
    url(r'^news/(?P<post_id>[0-9]+)/rate$', views.rate_post, name='rate_post'),
    url(r'^news/(?P<post_id>[0-9]+)/add_comment$', views.add_comment, name='add_comment'),
]
