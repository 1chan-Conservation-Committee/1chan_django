from django.db import models
from django.utils import timezone


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
    author_board = models.CharField(max_length=32, blank=True)
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


class Comment(models.Model):
    author_ip = models.GenericIPAddressField()
    author_board = models.CharField(max_length=32, blank=True)
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
