# core/context_processors.py
from .utils.nav import find_photo_index_page, find_album_index_page, find_book_index_page, find_blog_index_page

def global_nav(request):
    """
    Inject commonly used nav targets into every template context.
    Keep it lightweight; this runs on most responses.
    """
    return {
        "photo_index_page": find_photo_index_page(request),
        "album_index_page": find_album_index_page(request),
        "book_index_page": find_book_index_page(request),
        "blog_index_page": find_blog_index_page(request),
    }
