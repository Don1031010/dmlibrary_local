from django import template
register = template.Library()

LABELS = {"ja": "Japanese", "en": "English", "zh": "Chinese"}

@register.filter
def lang_label(code):
    return LABELS.get(code, str(code).upper())
