from django.contrib import admin
from .models import Post, Category, Comment, Smiley, Homeboard


admin.site.register([Post, Category, Comment, Smiley, Homeboard])
