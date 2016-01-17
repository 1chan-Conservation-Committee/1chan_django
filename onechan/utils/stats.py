from django_redis import get_redis_connection
from datetime import datetime, timedelta


def stats(request):
    conn = get_redis_connection('default')
    ts = datetime.now().timestamp()
    return {
        'stats_today_users': conn.scard('stats_today_users'),
        'stats_today_posts': conn.get('stats_today_posts'),
        'stats_speed': conn.zcount('stats_hour_posts', ts - 3600, ts)
    }

def get_tomorrow(dt=None):
    if not dt:
        dt = datetime.now()
    td = timedelta(days=1, hours=-dt.hour, minutes=-dt.minute, seconds=-dt.second)
    return dt + td

def update_posting_stats():
    conn = get_redis_connection('default')
    conn.incr('stats_today_posts')
    conn.expireat('stats_today_posts', get_tomorrow())
    ts = datetime.now().timestamp()
    conn.zremrangebyscore('stats_hour_posts', 0, ts - 3600)
    conn.zadd('stats_hour_posts', ts, ts)

def _get_viewer_set_name(mdl_inst):
    return 'viewers_{0.__class__.__name__!s}_{0.pk!s}'.format(mdl_inst)

def get_view_count(mdl_inst):
    conn = get_redis_connection('default')
    return conn.scard(_get_viewer_set_name(mdl_inst))

def update_view_count(mdl_inst, viewer):
    conn = get_redis_connection('default')
    conn.sadd(_get_viewer_set_name(mdl_inst), viewer)


class DailyUsersMiddleware(object):

    def process_request(self, request):
        host = request.META['REMOTE_ADDR']
        conn = get_redis_connection('default')
        conn.sadd('stats_today_users', host)
        conn.expireat('stats_today_users', get_tomorrow())
