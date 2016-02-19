from itertools import chain
from django.core.exceptions import ValidationError
import django.forms as forms
import django.forms.widgets as widgets
from django.utils.encoding import (
    force_str, force_text, python_2_unicode_compatible,
)
from django.utils.html import format_html, html_safe
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
from captcha.fields import ReCaptchaField
from .models import Post, Category, Comment, Homeboard


class CustomAttrsSelect(widgets.Select):

    def __init__(self, attrs=None, choices=(), ignore_field_choices=False):
        self._ignore_field_choices = ignore_field_choices
        if ignore_field_choices:
            self._own_choices = choices
            choices = ()
        super(CustomAttrsSelect, self).__init__(attrs, choices)

    def render_option(self, selected_choices, option_value, option_label, option_attrs):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html('<option value="{}"{}{}>{}</option>',
                           option_value,
                           selected_html,
                           flatatt(option_attrs),
                           force_text(option_label))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        if self._ignore_field_choices:
            choices = self._own_choices
        else:
            choices = chain(self.choices, choices)
        if callable(choices):
            choices = choices()
        for option in choices:
            output.append(self.render_option(selected_choices, *option))
        return '\n'.join(output)


class CategoryKeyField(forms.Field):

    def __init__(self, **kwargs):
        super(CategoryKeyField, self).__init__(**kwargs)

    def clean(self, value):
        if not value and not self.required:
            return None
        try:
            return Category.objects.get(key=value)
        except Category.DoesNotExist:
            raise ValidationError('Данная категория не существует')


def make_category_choices():
    return [('', '', {})] + [(cat.key, cat.name, {'data-category-descr': cat.desciption})
        for cat in Category.objects.filter(hidden=False)]

def make_homeboard_choices():
    return [('', '', {})] + [(board.pk, board.name, {'data-board-icon': board.img.url})
        for board in Homeboard.objects.all()]


class NewPostForm(forms.ModelForm):
    category = CategoryKeyField(
        required=False,
        widget=CustomAttrsSelect(
            choices=make_category_choices, attrs={'id': 'news_addform_category'},
            ignore_field_choices=True
        ),
    )
    captcha = ReCaptchaField()
    author_board = forms.ModelChoiceField(
        queryset=Homeboard.objects.all(),
        required=False,
        widget=CustomAttrsSelect(
            choices=make_homeboard_choices, attrs={'id': 'homeboard_select'},
            ignore_field_choices=True
        )
    )

    class Meta:
        model = Post
        fields = ['title', 'link', 'text', 'text_full', 'author_board', 'category']


class NewCommentForm(forms.ModelForm):
    captcha = ReCaptchaField()
    author_board = forms.ModelChoiceField(
        queryset=Homeboard.objects.all(),
        required=False,
        widget=CustomAttrsSelect(
            choices=make_homeboard_choices, attrs={'id': 'homeboard_select'},
            ignore_field_choices=True
        )
    )

    class Meta:
        model = Comment
        fields = ['text', 'author_board']
