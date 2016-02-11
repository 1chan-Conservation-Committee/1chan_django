from django import forms
from django.contrib import admin
from .models import Post, Category, Comment, Smiley, Homeboard


admin.site.register([Category, Comment, Smiley, Homeboard])


class PostApproverForm(forms.ModelForm):

    class Meta:
        fields = ['category', 'status', 'hide_reason', 'pinned', 'bumpable']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):

    list_display = ('pk', 'title', 'status', 'category')
    list_display_links = ('title',)

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            kwargs['form'] = PostApproverForm
        return super(PostAdmin, self).get_form(request, obj, **kwargs)
