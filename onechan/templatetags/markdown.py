import re
from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings
from django.utils.safestring import mark_safe
from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


register = template.Library()


class EscapeHtml(Extension):
    def extendMarkdown(self, md, md_globals):
        del md.preprocessors['html_block']
        del md.inlinePatterns['html']


class RestrictImageHosts(Extension):

    class ImageHostFilter(Treeprocessor):

        def __init__(self, md, patterns):
            super(RestrictImageHosts.ImageHostFilter, self).__init__(md)
            self.patterns = patterns

        def run(self, root):
            for image in root.findall('.//img'):
                link = image.get('src')
                if not any((pattern.match(link) for pattern in self.patterns)):
                    image.tag = 'a'
                    image.attrib.pop('src')
                    image.attrib.pop('alt')
                    image.text = link
                    image.set('href', link)


    def __init__(self, allowed_hosts_list):
        self.patterns = [re.compile(pattern) for pattern in allowed_hosts_list]
        super(RestrictImageHosts, self).__init__()

    def extendMarkdown(self, md, md_globals):
        md.treeprocessors.add('imagefilter', self.ImageHostFilter(md, self.patterns), '_end')


md = Markdown(extensions=[EscapeHtml(), RestrictImageHosts(settings.ALLOWED_IMAGE_PATTERNS)])

@register.filter
@stringfilter
def markdown(input):
    md.reset()
    return mark_safe(md.convert(input))
