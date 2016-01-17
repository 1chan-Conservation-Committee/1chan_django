from django.core.cache import cache
from .models import Smiley


class SmileyCacheMiddleware(object):

    def process_request(self, request):
        cache.set('smiley_list',
            { s.name: s.img.url for s in Smiley.objects.all() },
            timeout=None
        )

    def process_response(self, request, response):
        cache.delete('smiley_list')
        return response
