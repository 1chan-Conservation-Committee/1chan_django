from ..models import Post


def favourites(request):
    return {
        'favourites': list(Post.objects.filter(favourite__user_ip=request.META['REMOTE_ADDR']))
    }
