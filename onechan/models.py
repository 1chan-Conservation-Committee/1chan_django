from django.db import models
from django.utils import timezone
from .utils.stats import get_view_count, update_view_count


class Category(models.Model):
    key = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255, unique=True)
    desciption = models.TextField()
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Post(models.Model):
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
        return self.comment_set.select_related('author_board').order_by('pk')

    @property
    def view_count(self):
        return get_view_count(self)

    def add_viewer(self, ip):
        update_view_count(self, ip)


class Comment(models.Model):
    author_ip = models.GenericIPAddressField()
    author_board = models.ForeignKey('Homeboard', null=True, blank=True, on_delete=models.SET_NULL)
    pub_date = models.DateTimeField(default=timezone.now)
    text = models.TextField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    def __str__(self):
        return self.text if len(self.text) < 100 else self.text[:100] + '…'


class Rater(models.Model):
    ip = models.GenericIPAddressField()
    post = models.ForeignKey(Post)

    class Meta:
        unique_together = ('ip', 'post')


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