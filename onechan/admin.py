from django.contrib import admin
from .models import Post, Category, Comment, Smiley


admin.site.register([Post, Category, Comment, Smiley])
