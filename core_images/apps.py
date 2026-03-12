from django.apps import AppConfig


class CoreImagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_images'
    
    def ready(self):
        # swap the FilterSet used by /admin/images/
        from wagtail.images.views.images import IndexView as ImagesIndexView
        from .admin_filters import CustomImagesFilterSet
        ImagesIndexView.filterset_class = CustomImagesFilterSet
        