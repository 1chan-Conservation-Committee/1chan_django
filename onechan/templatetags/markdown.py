from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings
from django.utils.safestring import mark_safe
from markdown import Markdown
from markdown.extensions import Extension


register = template.Library()


class EscapeHtml(Extension):
    def extendMarkdown(self, md, md_globals):
        del md.preprocessors['html_block']
        del md.inlinePatterns['html']


md = Markdown(extensions=[EscapeHtml()])

@register.filter
@stringfilter
def markdown(input):
    md.reset()
    return mark_safe(md.convert(input))
