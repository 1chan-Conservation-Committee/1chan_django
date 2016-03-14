from itertools import chain
from django.core.exceptions import ValidationError
import django.forms as forms
import django.forms.widgets as widgets
from django.template.loader import render_to_string
from django.utils.encoding import (
    force_str, force_text, python_2_unicode_compatible,
)
from django.utils.html import format_html, html_safe
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
from captcha.fields import ReCaptchaField
from .models import *


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


class LazyCaptcha(forms.Widget):

    def __init__(self, captcha_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captcha = captcha_widget

    def render(self, name, value, attrs=None):
        return mark_safe(render_to_string('onechan/lazy_captcha.html', {
            'recaptcha': self.captcha.render(name, value, attrs),
            'check_required': self.check_required,
        }))

    def value_from_datadict(self, *args, **kwargs):
        return self.captcha.value_from_datadict(*args, **kwargs)


class LazyCaptchaField(ReCaptchaField):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = LazyCaptcha(self.widget)

    def clean(self, value):
        if not self.check_required:
            return True
        else:
            return super().clean(value)

    @property
    def check_required(self):
        return self._check_required

    @check_required.setter
    def check_required(self, value):
        self._check_required = value
        self.widget.check_required = value


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
    captcha = LazyCaptchaField()
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

    def __init__(self, *args, **kwargs):
        self.ip = kwargs.pop('ip')
        super().__init__(*args, **kwargs)
        captcha_field = self.fields['captcha']
        captcha_field.check_required = self.is_captcha_required(self.ip)

    @staticmethod
    def is_captcha_required(ip):
        comments_made = cache.get('onechan_captcha_comments_' + str(ip)) or 0
        return comments_made == 0


class NewLinkForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = Link
        fields = ['uri', 'title']


def make_reaction_choices():
    return [(r.pk, r.name, {'data-reaction-icon': r.img.url}) for r in ReactionImage.objects.all()]


class CommentReactionForm(forms.Form):
    image = forms.ModelChoiceField(
        queryset=ReactionImage.objects.all(),
        required=False,
        widget=CustomAttrsSelect(
            choices=make_reaction_choices, attrs={'id': 'reaction_select'},
            ignore_field_choices=True
        )
    )
