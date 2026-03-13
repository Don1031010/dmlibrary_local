# book/wagtail_hooks.py
from wagtail import hooks
from wagtail.admin.viewsets.pages import PageListingViewSet
from wagtail.admin.ui.tables import Column
from wagtail.admin.ui.tables.pages import PageTitleColumn  # ✅ import this

from .models import BookPage


# def categories_text(page: BookPage) -> str:
#     names = list(page.categories.values_list("name", flat=True))
#     return ", ".join(names) if names else "—"


# class BookPageListingViewSet(PageListingViewSet):
#     model = BookPage
#     add_to_admin_menu = True
#     menu_label = "Books"
#     icon = "book"

#     def get_queryset(self, request):
#         return super().get_queryset(request).prefetch_related("categories")

#     # ✅ Title is now clickable, like in Explorer
#     columns = [
#         PageTitleColumn("title", label="Title"),
#         Column("Author", accessor="author"),
#         Column("Categories", accessor=categories_text),
#         Column("Language", accessor="language"),
#         Column("Updated", accessor="latest_revision_created_at"),
#     ]

#     search_fields = ["title", "sub_title", "author", "publisher"]


# @hooks.register("register_admin_viewset")
# def register_book_page_listing():
#     return BookPageListingViewSet("books")
