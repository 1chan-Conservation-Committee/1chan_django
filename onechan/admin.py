from django.contrib import admin
from .models import Post, Category, Comment


admin.site.register([Post, Category, Comment])
