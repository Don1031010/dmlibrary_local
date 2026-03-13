from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.models import Page, Orderable, Collection
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel
from modelcluster.fields import ParentalManyToManyField 

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from wagtail.images import get_image_model
from taggit.models import Tag
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


class PhotoIndexPage(Page):
    template = "photo/photo_index_page.html"

    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        Image = get_image_model()

        # Base: all images in "photos" collection (incl. descendants)
        try:
            photos_collection = Collection.objects.get(name__iexact="photos")
            collections = photos_collection.get_descendants(inclusive=True)
            base_qs = Image.objects.filter(collection__in=collections)
        except Collection.DoesNotExist:
            collections = []
            base_qs = Image.objects.none()

        # Read filters
        q = (request.GET.get("q") or "").strip() or None
        selected_year = request.GET.get("year") or None
        selected_tags = [t for t in request.GET.getlist("tag") if t]

        # Apply non-search filters to the queryset FIRST
        if selected_year and hasattr(Image, "taken_at"):
            try:
                base_qs = base_qs.filter(taken_at__year=int(selected_year))
            except ValueError:
                pass

        # AND semantics for multiple tags (require all)
        for t in selected_tags:
            base_qs = base_qs.filter(tags__name=t)

        # Now decide search vs. ordering
        if q:
            results = base_qs.search(q)  # relevance order, do NOT order_by here

            # If Postgres FTS can’t tokenize Japanese and returns 0, fallback to icontains
            if len(results) == 0:
                qs = base_qs.filter(
                    Q(title__icontains=q) |
                    Q(tags__name__icontains=q)
                ).distinct().order_by("-created_at")
            else:
                qs = results  # let paginator handle SearchResults
        else:
            qs = base_qs.order_by("-created_at")

        # Facets
        available_years = []
        if collections and hasattr(Image, "taken_at"):
            year_dates = (
                Image.objects
                .filter(collection__in=collections, taken_at__isnull=False)
                .dates("taken_at", "year", order="DESC")
            )
            available_years = [d.year for d in year_dates]

        ct = ContentType.objects.get_for_model(Image)
        available_tags = (
            Tag.objects.filter(
                taggit_taggeditem_items__content_type=ct,
                taggit_taggeditem_items__object_id__in=Image.objects
                    .filter(collection__in=collections)
                    .values("id")
            )
            .distinct()
            .order_by("name")
        ) if collections else Tag.objects.none()

        # Pagination
        paginator = Paginator(qs, 24)
        page_num = request.GET.get("page", 1)
        try:
            images_page = paginator.page(page_num)
        except PageNotAnInteger:
            images_page = paginator.page(1)
        except EmptyPage:
            images_page = paginator.page(paginator.num_pages)

        context.update({
            "images": images_page,
            "q": q,
            "available_years": available_years,
            "available_tags": available_tags,
            "selected_year": int(selected_year) if selected_year else None,
            "selected_tags": selected_tags,
        })
        return context


class AlbumIndexPage(Page):
    template = "photo/album_index_page.html"
    subpage_types = ["photo.PhotoAlbumPage"]


class PhotoAlbumPage(Page):
    template = "photo/photo_album_page.html"
    parent_page_types = ["photo.AlbumIndexPage"] 
    description = RichTextField(blank=True)
    content_panels = Page.content_panels + [
        FieldPanel("description"),
        InlinePanel("items", label="Photos"),
    ]


class PhotoAlbumItem(Orderable):
    page = ParentalKey(PhotoAlbumPage, related_name="items", on_delete=models.CASCADE)
    image = models.ForeignKey(get_image_model(), null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="+")
    caption = models.CharField(max_length=255, blank=True)
    panels = [FieldPanel("image"), FieldPanel("caption")]
