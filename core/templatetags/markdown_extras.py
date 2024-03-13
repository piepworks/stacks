from django.template.defaulttags import register
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
import markdown as md
import bleach


@register.filter()
@stringfilter
def markdown(value):
    bleach.sanitizer.ALLOWED_TAGS.append("br")

    return mark_safe(
        bleach.clean(
            md.markdown(
                value,
                extensions=[
                    "markdown.extensions.fenced_code",
                    "markdown.extensions.smarty",
                ],
            ),
        )
    )
