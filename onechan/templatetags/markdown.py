import re
from django import template
from django.template.defaultfilters import stringfilter
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.core.urlresolvers import reverse
from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.inlinepatterns import Pattern
from markdown.util import etree
from ..models import Comment


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
                if not any((pattern.match(link) for pattern in self.patterns)) and\
                        'smiley' not in image.get('class'):
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


class Smileys(Extension):

    class SmileysPattern(Pattern):
        def __init__(self):
            Pattern.__init__(self, '')

        def getCompiledRegExp(self):
            self.smileys = cache.get('smiley_list')
            return re.compile(r'^(.*?):(?P<smiley>' + '|'.join(self.smileys.keys()) + '):(.*?)$')

        def handleMatch(self, m):
            smiley_name = m.group('smiley')
            el = etree.Element('img', src=self.smileys[smiley_name])
            el.set('class', 'smiley')
            return el

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('smileys', self.SmileysPattern(), '_end')
        md.ESCAPED_CHARS.append(':')


class Spoilers(Extension):

    class SpoilerPattern(Pattern):

        def __init__(self):
            Pattern.__init__(self, r'(%{2})(?P<contents>.+?)\2')

        def handleMatch(self, m):
            el = etree.Element('span')
            el.set('class', 'spoiler')
            el.text = m.group('contents')
            return el

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('spoilers', self.SpoilerPattern(), '_end')
        md.ESCAPED_CHARS.append('%')


class CommentRefs(Extension):

    class CommentRefPattern(Pattern):

        def __init__(self):
            Pattern.__init__(self, r'(>{2})(?P<comment_id>\d+)')

        def handleMatch(self, m):
            comment_id = int(m.group('comment_id'))
            try:
                comment = Comment.objects.get(pk=comment_id)
                el = etree.Element('a')
                el.set('href', '{}#{}'.format(
                    reverse('onechan:show_post', kwargs={
                        'post_id': comment.post_id
                    }),
                    comment_id
                ))
                el.set('class', 'comment-ref')
                el.set('data-comment-url',
                    reverse('onechan:get_comment', kwargs={'comment_id': comment_id})
                )
                el.text = '>>{}'.format(comment_id)
                return el
            except Exception:
                return '>>{}'.format(comment_id)

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('comment_refs', self.CommentRefPattern(), '_end')


md = Markdown(extensions=[
    EscapeHtml(),
    RestrictImageHosts(settings.ALLOWED_IMAGE_PATTERNS),
    Smileys(),
    Spoilers(),
    CommentRefs(),
])

# sorry mommy i am a dirty monkey patcher
md.parser.blockprocessors['quote'].RE = re.compile(r'(^|\n)[ ]{0,3}>(?!\>\d)[ ]?(.*)')

@register.filter
@stringfilter
def markdown(input):
    md.reset()
    return mark_safe(md.convert(input))
