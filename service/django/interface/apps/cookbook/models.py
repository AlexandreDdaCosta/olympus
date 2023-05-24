from django.db import models


class Media(models.Model):
    description = models.CharField(max_length=255,
                                   null=False)
    url_path = models.URLField(max_length=200,
                               null=False,
                               unique=True)

    def __unicode__(self):
        return '%s' % (self.url_path)


class Author(models.Model):
    name = models.CharField(max_length=255,
                            null=False,
                            unique=True)
    biography = models.TextField(null=False)
    photo = models.ForeignKey(Media,
                              on_delete=models.CASCADE)

    def __unicode__(self):
        return '%s' % (self.name)


class Course(models.Model):
    name = models.CharField(max_length=255,
                            null=False,
                            unique=True)
    book_order = models.PositiveIntegerField(null=False,
                                             unique=True)


class Recipe(models.Model):
    course = models.ForeignKey(Course,
                               null=False,
                               on_delete=models.CASCADE)
    course_order = models.PositiveIntegerField(null=False,
                                               unique=True)
    title = models.CharField(max_length=255,
                             null=False)
    introduction = models.TextField(null=False)
    postscript = models.TextField(null=True)


class RecipeAuthor(models.Model):
    author = models.ForeignKey(Author,
                               null=False,
                               on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,
                               null=False,
                               on_delete=models.CASCADE)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,
                               null=False,
                               on_delete=models.CASCADE)
    ingredient_order = models.PositiveIntegerField(null=False,
                                                   unique=True)
    ingredient = models.CharField(db_index=True,
                                  max_length=255,
                                  null=False)
    description = models.TextField(null=True)


class RecipeInstruction(models.Model):
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE)
    instruction_order = models.PositiveIntegerField(null=False,
                                                    unique=True)
    header = models.CharField(max_length=255,
                              null=True)
    instruction = models.TextField(null=False)


class RecipeMedia(models.Model):
    recipe = models.ForeignKey(Recipe,
                               null=False,
                               on_delete=models.CASCADE)
    media = models.ForeignKey(Media,
                              null=False,
                              on_delete=models.CASCADE)
    bold_caption = models.CharField(max_length=255,
                                    null=True)
    caption = models.TextField(null=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'media'],
                                    name='recipe_illustration'),
        ]
