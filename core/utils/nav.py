# core/utils/nav.py
from typing import Optional, Type
from django.core.cache import cache
from django.db.models import Model, Case, When, IntegerField
from wagtail.models import Site

# import your page subclasses
from photo.models import PhotoIndexPage, AlbumIndexPage  # adjust to your app layout
from book.models import BookIndexPage  # if you want a book index finder
from blog.models import BlogIndexPage  # if you want a blog index finder

CACHE_TTL = 300  # seconds; set 0/None to disable caching

# TODO:
# If you want, I can add Wagtail publish/unpublish/move signal hooks to invalidate these cache keys automatically.
#

def _find_index_page(request, page_model, prefer_slug=None, cache_key_prefix=None):
    site = Site.find_for_request(request)
    if not site:
        return None

    # cache key
    page_id = None
    if CACHE_TTL and cache_key_prefix:
        root_locale = getattr(site.root_page, "locale", None)
        ck = f"{cache_key_prefix}:{site.id}:{getattr(root_locale, 'id', 'none')}:{prefer_slug or '-'}"
        page_id = cache.get(ck)
        if page_id:
            try:
                return page_model.objects.specific().get(id=page_id)
            except page_model.DoesNotExist:
                cache.delete(ck)

    # Important: drop `.public()` so restricted pages are included
    qs = (
        page_model.objects
        .live()
        .in_site(site)
        .specific()
    )

    root_locale = getattr(site.root_page, "locale", None)
    if root_locale:
        qs = qs.filter(locale=root_locale)

    if prefer_slug:
        qs = qs.order_by(
            Case(When(slug=prefer_slug, then=0), default=1, output_field=IntegerField()),
            "path",
        )
    else:
        qs = qs.order_by("path")

    # For anonymous users, prefer a public page if one exists; otherwise fall back to restricted.
    if request.user.is_authenticated:
        page = qs.first()
    else:
        page = qs.public().first() or qs.first()

    if CACHE_TTL and cache_key_prefix and page:
        cache.set(ck, page.id, CACHE_TTL)

    return page

# def _find_index_page(
#     request,
#     page_model: Type[Model],
#     prefer_slug: Optional[str] = None,
#     cache_key_prefix: Optional[str] = None,
# ):
#     """
#     Generic resolver for the first live/public page of a given model under the current Site,
#     preferring the site's locale when present and (optionally) a specific slug.

#     Returns None if not found.
#     """
#     site = Site.find_for_request(request)
#     if not site:
#         return None

#     # cache by site + locale + model + optional preferred slug
#     if CACHE_TTL and cache_key_prefix:
#         root_locale = getattr(site.root_page, "locale", None)
#         ck = f"{cache_key_prefix}:{site.id}:{getattr(root_locale, 'id', 'none')}:{prefer_slug or '-'}"
#         page_id = cache.get(ck)
#         if page_id:
#             try:
#                 return page_model.objects.specific().get(id=page_id)
#             except page_model.DoesNotExist:
#                 cache.delete(ck)

#     qs = (
#         page_model.objects
#         .live()
#         .public()
#         .in_site(site)
#         .specific()
#     )

#     root_locale = getattr(site.root_page, "locale", None)
#     if root_locale:
#         qs = qs.filter(locale=root_locale)

#     if prefer_slug:
#         qs = qs.order_by(
#             Case(
#                 When(slug=prefer_slug, then=0),
#                 default=1,
#                 output_field=IntegerField(),
#             ),
#             "path",  # fall back to nearest-to-root
#         )

#     page = qs.first()

#     if CACHE_TTL and cache_key_prefix and page:
#         cache.set(ck, page.id, CACHE_TTL)

#     return page


def find_photo_index_page(request):
    # prefer a canonical slug if you use one; otherwise omit prefer_slug
    return _find_index_page(
        request,
        page_model=PhotoIndexPage,
        prefer_slug="photos",
        cache_key_prefix="photo_index",
    )


def find_album_index_page(request):
    return _find_index_page(
        request,
        page_model=AlbumIndexPage,
        prefer_slug="albums",
        cache_key_prefix="album_index",
    )

def find_book_index_page(request):
    return _find_index_page(
        request,
        page_model=BookIndexPage,
        prefer_slug="books",
        cache_key_prefix="book_index",
    )   
    
def find_blog_index_page(request):
    return _find_index_page(
        request,
        page_model=BlogIndexPage,
        prefer_slug="blog",
        cache_key_prefix="blog_index",
    )