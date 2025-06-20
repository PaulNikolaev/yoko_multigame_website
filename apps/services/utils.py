from uuid import uuid4
from pytils.translit import slugify


def unique_slugify(instance, text_to_slugify):
    """
    Генератор уникальных SLUG для моделей, в случае существования такого SLUG.
    """
    model = instance.__class__
    if instance.slug:
        base_slug = instance.slug
    else:
        base_slug = slugify(text_to_slugify)

    unique_slug = base_slug

    while model.objects.filter(slug=unique_slug).exclude(pk=instance.pk).exists():
        unique_slug = f"{base_slug}-{uuid4().hex[:8]}"

    return unique_slug