from django.conf import settings
from django.db import models
from django.utils.text import slugify

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.models import Page, Orderable, Collection
from wagtail.fields import StreamField, RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock
from modelcluster.fields import ParentalManyToManyField  # NEW
from wagtail.embeds.blocks import EmbedBlock

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from wagtail.images import get_image_model
from taggit.models import Tag
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Count
from wagtail.search import index

# ---------- BLOG ----------
class BlogIndexPage(Page):
    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro")]
    template = "blog/blog_index_page.html"
    # optional, but helps enforce tree
    subpage_types = ["blog.BlogPostPage"]
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Base queryset: this index's BlogPostPage children
        # base_qs = (
        #     self.get_children()
        #     .live()
        #     .specific()
        #     .type(BlogPostPage)            # only blog posts
        # )
        
        
        base_qs = (
            BlogPostPage.objects.live()
            # .public()
            .descendant_of(self)
        )
        base_qs = base_qs.prefetch_related("tags")
        
        # Filters
        q = (request.GET.get("q") or "").strip() or None
        selected_tags = [t for t in request.GET.getlist("tag") if t]

        # Tag filter (OR semantics; change to AND by looping over names)
        if selected_tags:
            base_qs = base_qs.filter(tags__name__in=selected_tags).distinct()

        # Search: use Wagtail search; fall back to icontains for Japanese substrings
        if q:
            results = base_qs.search(q)   # relevance order; don't order_by on SearchResults

            if len(results) == 0:
                # Fallback for Japanese partial matching
                qs = (
                    base_qs.filter(
                        Q(title__icontains=q) |
                        Q(tags__name__icontains=q)
                    )
                    .distinct()
                    .order_by("-first_published_at")
                )
            else:
                qs = results
        else:
            qs = base_qs.order_by("-first_published_at")

        # Facet: all tags that appear in this index
        # ct = ContentType.objects.get_for_model(BlogPostPage)
        # available_tags = (
        #     Tag.objects.filter(
        #         taggit_taggeditem_items__content_type=ct,
        #         # taggit_taggeditem_items__object_id__in=self.get_children()
        #         #     .live()
        #         #     .values("id")
        #         taggit_taggeditem_items__object_id__in=base_qs.values_list("id", flat=True),

        #     )
        #     .distinct()
        #     .order_by("name")
        # )
        available_tags = (
            Tag.objects
            .filter(blogpostpage__in=base_qs)
            .annotate(num_posts=Count("blogpostpage", distinct=True))
            .order_by("name")
        )
        # Pagination
        paginator = Paginator(qs, 10)  # 10 posts per page
        page_num = request.GET.get("page", 1)
        try:
            posts = paginator.page(page_num)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)

        context.update({
            "posts": posts,
            "q": q,
            "available_tags": available_tags,
            "selected_tags": selected_tags,
        })
        return context
    
    
class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey("BlogPostPage", related_name="tagged_items", on_delete=models.CASCADE)

class GalleryImage(Orderable):
    page = ParentalKey("BlogPostPage", related_name="gallery", on_delete=models.CASCADE)
    image = models.ForeignKey("core_images.CustomImage", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    caption = models.CharField(max_length=255, blank=True)
    panels = [FieldPanel("image"), FieldPanel("caption")]

class BlogPostPage(Page):
    template = "blog/blog_post_page.html"
    # optional, but helps enforce tree
    parent_page_types = ["blog.BlogIndexPage"]    
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                               on_delete=models.SET_NULL, related_name="wagtail_posts")
    body = StreamField(
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
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    categories = ParentalManyToManyField("cms_taxonomy.BlogCategory", blank=True)  # NEW
    content_panels = Page.content_panels + [
        FieldPanel("author"),
        FieldPanel("tags"),
        FieldPanel("categories"),  # NEW
        FieldPanel("body"),
        InlinePanel("gallery", label="Gallery"),
    ]
    
    # Make search + tag filters work (and improve partial matches)
    search_fields = Page.search_fields + [
        index.SearchField("title", partial_match=True),
        index.SearchField("body", partial_match=True),
        index.RelatedFields(
            "tags",
            [index.FilterField("name"), index.SearchField("name", partial_match=True)],
        ),
    ]    
