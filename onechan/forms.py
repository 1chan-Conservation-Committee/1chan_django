import django.forms as forms
from captcha.fields import ReCaptchaField
from .models import Post, Category, Comment

def make_category_choices():
    return [('', '')] + [(cat.key, cat.name) for cat in Category.objects.filter(hidden=False)]


class NewPostForm(forms.ModelForm):
    category = forms.ChoiceField(choices=make_category_choices, required=False)
    captcha = ReCaptchaField()

    class Meta:
        model = Post
        fields = ['title', 'link', 'text', 'text_full']


class NewCommentForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = Comment
        fields = ['text']
