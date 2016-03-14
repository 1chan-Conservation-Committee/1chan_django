from django.db import models
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from .utils.stats import get_view_count, update_view_count


class PubDateUtilMixin(object):

    def is_pubdate_within_week(self):
        delta = timezone.now() - self.pub_date
        return delta.days < 7


class Category(models.Model):
    key = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255, unique=True)
    desciption = models.TextField()
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Post(PubDateUtilMixin, models.Model):
    title = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    text_full = models.TextField(blank=True)
    author_ip = models.GenericIPAddressField()
    author_board = models.ForeignKey('Homeboard', null=True, blank=True, on_delete=models.SET_NULL)
    pub_date = models.DateTimeField(default=timezone.now)
    bump_date = models.DateTimeField(default=timezone.now)
    rating = models.SmallIntegerField(default=0)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)

    bumpable = models.BooleanField(default=True)
    rateable = models.BooleanField(default=True)
    closed = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False)


    ALL = 0
    APPROVED = 1
    HIDDEN = 2
    status_choices = (
        (ALL, 'All'),
        (APPROVED, 'Approved'),
        (HIDDEN, 'Hidden')
    )
    status = models.PositiveSmallIntegerField(choices=status_choices, default=ALL)
    hide_reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.title

    @property
    def favicon(self):
        if self.link and self.link.startswith(('https', 'http')):
            return "https://www.google.com/s2/favicons?domain=" + self.link

    def rate(self, rater_ip, value):
        if not self.rateable or Rater.objects.filter(ip=rater_ip, post=self).exists():
            return False
        else:
            Rater.objects.create(ip=rater_ip, post=self)
            self.rating = models.F('rating') + value
            self.save()
            self.refresh_from_db()
            return True

    def set_favourite(self, user_ip, value):
        if value:
            Favourite.objects.get_or_create(user_ip=user_ip, post=self)
        else:
            Favourite.objects.filter(user_ip=user_ip, post=self).delete()

    @property
    def favourers(self):
        if not hasattr(self, '_favourers'):
            self._favourers = self.objects.favourite_set.values_list('user_ip', flat=True)
        return self._favourers

    @property
    def comments(self):
        return self.comment_set.select_related('author_board')\
            .prefetch_related('reaction_set__image').order_by('pk')

    @property
    def view_count(self):
        return get_view_count(self)

    def add_viewer(self, ip):
        update_view_count(self, ip)


class Comment(PubDateUtilMixin, models.Model):
    author_ip = models.GenericIPAddressField()
    author_board = models.ForeignKey('Homeboard', null=True, blank=True, on_delete=models.SET_NULL)
    pub_date = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    reactors = models.ManyToManyField('AnonUser', through='Reaction')

    def save(self):
        super().save()
        comments_made = cache.get('onechan_captcha_comments_' + str(self.author_ip)) or 0
        cache.set('onechan_captcha_comments_' + str(self.author_ip),
            (comments_made + 1) % (settings.COMMENTS_WITHOUT_CAPTCHA + 1))

    @property
    def reactions(self):
        racts = {}
        for reaction in self.reaction_set.all():
            name = reaction.image.name
            if name in racts:
                racts[name]['count'] += 1
            else:
                racts[name] = {
                    'name': name,
                    'url': reaction.image.img.url,
                    'count': 1
                }

        return sorted(racts.values(), key=lambda r: (r['count'], r['name']), reverse=True)[:3]

    def __str__(self):
        return self.text if len(self.text) < 100 else self.text[:100] + '…'


class Link(models.Model):
    author = models.ForeignKey('AnonUser')
    pub_date = models.DateTimeField(default=timezone.now, db_index=True)
    uri = models.CharField(max_length=256)
    title = models.CharField(max_length=128)
    rating = models.SmallIntegerField(default=0)
    raters = models.ManyToManyField('AnonUser', related_name='rated_links')

    def __str__(self):
        return self.title


# TODO: rework into m2m relation between Post and AnonUser
class Rater(models.Model):
    ip = models.GenericIPAddressField()
    post = models.ForeignKey(Post)

    class Meta:
        unique_together = ('ip', 'post')


# TODO: rework into m2m relation between Post and AnonUser
class Favourite(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user_ip = models.GenericIPAddressField()

    class Meta:
        unique_together = ('user_ip', 'post')


class Smiley(models.Model):
    name = models.CharField(max_length=32, unique=True)
    img = models.FileField(upload_to='smileys/')

    def __str__(self):
        return self.name


class Homeboard(models.Model):
    name = models.CharField(max_length=64, unique=True)
    img = models.FileField(upload_to='homeboards/')

    def __str__(self):
        return self.name


class AnonUser(models.Model):
    ip = models.GenericIPAddressField(unique=True)

    def __str__(self):
        return str(self.ip)


class ReactionImage(models.Model):
    name = models.CharField(max_length=64, unique=True)
    img = models.FileField(upload_to='reactions/')

    def __str__(self):
        return self.name


class Reaction(models.Model):
    user = models.ForeignKey(AnonUser, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    image = models.ForeignKey(ReactionImage, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'comment')
