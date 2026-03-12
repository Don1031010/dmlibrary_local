
from django.db import models
from django.utils.text import slugify
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel
from wagtail.search import index

class BaseCategory(index.Indexed, models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True)
    description = models.TextField(blank=True)

    panels = [FieldPanel("name"), FieldPanel("slug"), FieldPanel("description")]
    search_fields = [index.SearchField("name"), index.SearchField("description")]

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name

@register_snippet
class BlogCategory(BaseCategory):
    pass

# @register_snippet
# class PhotoCategory(BaseCategory):
#     pass

@register_snippet
class BookCategory(BaseCategory):
    pass
