from django.db import models
from wagtail.images.models import AbstractImage, AbstractRendition, Image
from wagtail.search import index
# from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension
# from django.db import migrations

class CustomImage(AbstractImage):
    taken_at = models.DateField(null=True, blank=True)

    admin_form_fields = Image.admin_form_fields + ("taken_at", )
    
    # IMPORTANT: include filter/search fields used by your views
    search_fields = Image.search_fields + [
        # allow free-text search on title and let partial match work better
        index.SearchField("title", partial_match=True),

        # filters you apply in code:
        index.FilterField("taken_at"),
        index.FilterField("collection_id"),

        # tags (related)
        index.RelatedFields(
            "tags",
            [
                index.FilterField("name"),
                index.SearchField("name", partial_match=True),
            ],
        ),
    ]

class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name="renditions")
    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)



# class Migration(migrations.Migration):
#     dependencies = [
#         ("core_images", "000X_previous"),
#     ]
#     operations = [
#         TrigramExtension(),
#         UnaccentExtension(),
#     ]
    