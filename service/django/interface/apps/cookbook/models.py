from django.db import models
from django.core.validators import MinValueValidator


def only_filename(filename):
    return filename


class Graphic(models.Model):
    url_path = models.URLField(max_length=255,
                               null=False)
    name = models.CharField(max_length=255,
                            null=False)
    caption = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['url_path', 'name'],
                                    name='unique_graphic'),
        ]

    def __unicode__(self):
        return '%s/%s' % (self.url_path, self.name)


class Author(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=False)
    photo = models.ForeignKey(Graphic,
                              on_delete=models.CASCADE)


class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=False)


class Recipe(models.Model):
    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    course_order = models.IntegerField(MinValueValidator(1),
                                       null=False,
                                       unique=True)
    title = models.CharField(max_length=255,
                             null=False)
    introduction = models.TextField(null=False)
    postscript = models.TextField(null=True)


class RecipeInstructions(models.Model):
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE)
    instruction_order = models.IntegerField(MinValueValidator(1),
                                            null=False,
                                            unique=True)
    header = models.CharField(max_length=255,
                              null=True)


class RecipeGraphic(models.Model):
    caption = models.CharField(max_length=255,
                               null=True)
    url = models.URLField(max_length=255)

    def __unicode__(self):
        return '%s' % (self.url)
