from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext as _

class Graphic(models.Model):
    caption = models.CharField(max_length=255)
    label = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    url_source = models.URLField(max_length=255)

    def __unicode__(self):
        return '%s' % (self.url)

class Topic(models.Model):
    description = models.CharField(max_length=255)
    graphic = models.ForeignKey(Graphic,on_delete=models.CASCADE)
    name = models.CharField(db_index=True,max_length=30,unique=True,default="/")

    def __unicode__(self):
        return '%s' % (self.name)

class Article(models.Model):
    author = models.ForeignKey(User,on_delete=models.CASCADE)
    body = models.TextField(null=True)
    create_date = models.DateTimeField(_('Created'), auto_now_add=True)
    featured = models.BooleanField(blank=True,default=False)
    featured_graphic = models.ForeignKey(Graphic,on_delete=models.CASCADE,null=True)
    graphics = models.ManyToManyField(Graphic,related_name='article_graphics')
    published = models.BooleanField(blank=True,default=False)
    summary = models.TextField(null=True)
    title = models.CharField(db_index=True,max_length=255)
    topic = models.ForeignKey(Topic,on_delete=models.CASCADE)

    def __unicode__(self):
        return '%s' % (self.title)

class Article_Revision(models.Model):
    archive_date = models.DateTimeField(_('Archived'),auto_now_add=True)
    article = models.ForeignKey(Article,on_delete=models.CASCADE)
    body = models.TextField(null=True)
    summary = models.TextField(null=True)
    title = models.CharField(db_index=True,max_length=255)
    topic = models.ForeignKey(Topic,on_delete=models.CASCADE,null=True)

    def __unicode__(self):
        return '%s' % (self.title)

class Keyword(models.Model):
    hashtag = models.BooleanField(blank=True,default=False)
    name = models.CharField(db_index=True,max_length=255)

    def __unicode__(self):
        return '%s' % (self.name)

class Keyword_Article(models.Model):
    article = models.ForeignKey(Article,on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword,on_delete=models.CASCADE)
    occurrences = models.PositiveIntegerField()

    def __unicode__(self):
        return '%s' % (self.id)
