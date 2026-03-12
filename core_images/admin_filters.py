# core_images/admin_filters.py
from django_filters import ChoiceFilter, CharFilter
from wagtail.images import get_image_model
# inherit the built-in images filterset so we keep default filters
from wagtail.images.views.images import ImagesFilterSet

Image = get_image_model()

class CustomImagesFilterSet(ImagesFilterSet):
    # empty choices for now; we’ll fill them dynamically in __init__
    year = ChoiceFilter(label="Year (taken_at)", method="filter_year", choices=[])
    title = CharFilter(field_name="title", lookup_expr="icontains", label="Title contains")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Build year choices from existing images (DESC order)
        qs = Image.objects.exclude(taken_at__isnull=True).dates("taken_at", "year", order="DESC")
        self.filters["year"].field.choices = [("", "— Any year —")] + [(d.year, str(d.year)) for d in qs]

    def filter_year(self, queryset, name, value):
        if value:
            return queryset.filter(taken_at__year=value)
        return queryset

    class Meta(ImagesFilterSet.Meta):
        model = Image  # keep whatever the project’s image model is (your CustomImage)
        
