from django.conf import settings
from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.models import Page
from wagtail.fields import StreamField, RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from modelcluster.fields import ParentalManyToManyField  # NEW
from wagtail.embeds.blocks import EmbedBlock

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from cms_taxonomy.models import BookCategory  # adjust to your app path
from django.utils.translation import gettext_lazy as _ 


LANGUAGE_CHOICES = [
    ("ja", "日本語"),
    ("en", "英語"),
    ("zh", "中国語"),
]
    
class BookIndexPage(Page):
    template = "book/book_index_page.html"
    subpage_types = ['book.BookPage']  # only allow BookPages inside

    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Base queryset: BookPage under this index
        books = (
            # BookPage.objects.live().public() #drop .public() to include restricted pages
            BookPage.objects.live()
            .descendant_of(self)
            .order_by("-first_published_at")
        )

        # Params
        q = (request.GET.get("q") or "").strip() or None
        tag = (request.GET.get("tag") or "").strip() or None
        category_slug = (request.GET.get("category") or "").strip() or None
        language = (request.GET.get("lang") or "").strip() or None

        # Optional search (substring match, Japanese-friendly)
        if q:
            books = books.filter(
                Q(title__icontains=q) |
                Q(sub_title__icontains=q) |
                Q(author__icontains=q) |
                Q(description__icontains=q)
            )

        if tag:
            books = books.filter(tags__name=tag)

        if category_slug:
            books = books.filter(categories__slug=category_slug)

        if language:
            books = books.filter(language=language)

        # Build filter option lists limited to this index scope
        # Categories actually used by pages under this index:
        used_category_ids = (
            BookPage.objects.live()
            .descendant_of(self)
            .values_list("categories__id", flat=True)
            .distinct()
        )
        category_options = (
            BookCategory.objects.filter(id__in=used_category_ids)
            .order_by("name")
        )

        # Languages actually used under this index:
        # language_options = (
        #     BookPage.objects.live()
        #     .descendant_of(self)
        #     .values_list("language", flat=True)
        #     .exclude(language__isnull=True)
        #     .exclude(language__exact="")
        #     .distinct()
        #     .order_by()
        # )
        language_options = LANGUAGE_CHOICES

        # Pagination
        page_number = request.GET.get("page", 1)
        paginator = Paginator(books, 12)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        context.update({
            "books": page_obj,
            "q": q,
            "active_tag": tag,
            "active_category": category_slug,
            "active_language": language,
            "category_options": category_options,
            "language_options": language_options,
        })
        return context
    
    
class BookPageTag(TaggedItemBase):
    content_object = ParentalKey("BookPage", related_name="tagged_items", on_delete=models.CASCADE)

class BookPage(Page):
    template = "book/book_page.html"
    parent_page_types = ['book.BookIndexPage']

    
    sub_title = models.CharField(max_length=255, blank=True)
    author = models.CharField(max_length=255, db_index=True)
    publisher = models.CharField(max_length=255, blank=True)
    published_date = models.DateField(null=True, blank=True)
    edition = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="ja")
    # language = models.CharField(max_length=10, default="ja")
    cover_image = models.ForeignKey("core_images.CustomImage", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="+")
    owner_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="wagtail_books")

    # RichText as a block (future-proof for mixing images/docs/embeds)
    description = StreamField(
        [
            ("text", blocks.RichTextBlock(features=[
                "h2","h3","bold","italic","ol","ul","link","hr","code","blockquote"
            ])),
            ("image", ImageChooserBlock()),
            ("document", DocumentChooserBlock()),
            ("embed", EmbedBlock()),
        ],
        use_json_field=True, blank=True,
    )

    tags = ClusterTaggableManager(through=BookPageTag, blank=True)

    categories = ParentalManyToManyField("cms_taxonomy.BookCategory", blank=True)  # NEW
    content_panels = Page.content_panels + [
        FieldPanel("sub_title"),
        FieldPanel("author"),
        FieldPanel("publisher"),
        FieldPanel("published_date"),
        FieldPanel("edition"),
        FieldPanel("language"),
        FieldPanel("cover_image"),
        FieldPanel("tags"),
        FieldPanel("categories"),  # NEW
        FieldPanel("description"),
        FieldPanel("owner_user"),
    ]
    

        
