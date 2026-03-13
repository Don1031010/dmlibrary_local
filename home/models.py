from django.db import models
from django.utils import timezone

from wagtail.models import Page
from wagtail.images import get_image_model


class HomePage(Page):
    template = "home/home_page.html"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        from book.models import BookPage
        from blog.models import BlogPostPage
        from photo.models import PhotoAlbumPage
        from wagtail.models import Collection

        Image = get_image_model()

        # Latest photos — Photos collection only (incl. descendants)
        try:
            photos_collection = Collection.objects.get(name__iexact="photos")
            collections = photos_collection.get_descendants(inclusive=True)
            context["latest_photos"] = (
                Image.objects.filter(collection__in=collections).order_by("-created_at")[:8]
            )
        except Collection.DoesNotExist:
            context["latest_photos"] = Image.objects.none()

        context["latest_albums"] = (
            PhotoAlbumPage.objects.live().order_by("-first_published_at")[:4]
        )
        context["latest_posts"] = (
            BlogPostPage.objects.live().order_by("-first_published_at")[:4]
        )
        context["latest_books"] = (
            BookPage.objects.live().order_by("-first_published_at")[:4]
        )

        # On This Day: same month/day, previous years only
        today = timezone.localdate()
        context["on_this_day"] = (
            Image.objects
            .filter(taken_at__month=today.month, taken_at__day=today.day)
            .exclude(taken_at__year=today.year)
            .order_by("taken_at")
        )
        context["today"] = today

        return context
