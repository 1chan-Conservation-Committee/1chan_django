from django.conf.urls import url
from . import views
# Create your views here.

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r"^news$", views.PostsListView.as_view(), {'posts_type': 'approved'}, name='approved_posts'),
    url(r"^news/all$", views.PostsListView.as_view(), {'posts_type': 'all'}, name='all_posts'),
    url(r"^news/hidden$", views.PostsListView.as_view(), {'posts_type': 'hidden'}, name='hidden_posts'),
    url(r'^news/favourites$', views.FavouritesListView.as_view(), name='favourite_posts'),
    url(r'^news/category/(?P<category_id>\d+)$', views.CategoryListView.as_view(), name='category_posts'),

    url(r'^categories$', views.category_list, name='category_list'),

    url(r'^news/(?P<post_id>[0-9]+)$', views.show_post, name='show_post'),
    url(r'^news/add$', views.add_post, name='add_post'),
    url(r'^news/(?P<post_id>[0-9]+)/rate$', views.rate_post, name='rate_post'),
    url(r'^news/(?P<post_id>[0-9]+)/add_comment$', views.add_comment, name='add_comment'),
    url(r'^news/(?P<post_id>[0-9]+)/set_favourite$', views.set_favourite, name='set_favourite'),

    url(r'^comments$', views.last_comments, name='last_comments'),
    url(r'^comments/(?P<comment_id>[0-9]+)$', views.get_comment, name='get_comment'),
    url(r'^comments/(?P<comment_id>[0-9]+)/react$', views.comment_react, name='comment_react'),

    url(r'^rss/news$', views.NewsFeed(), name='news_feed'),
    url(r'^rss/news/all$', views.NewsFeed(all=True), name='news_all_feed'),

    url(r'^help/markup$', views.markup_help, name='help_markup'),
]
