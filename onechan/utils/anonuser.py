from ..models import AnonUser


class AnonUserMiddleware(object):

    def process_request(self, request):
        ip = request.META['REMOTE_ADDR']
        request.anon_user, _ = AnonUser.objects.get_or_create(ip=ip)
