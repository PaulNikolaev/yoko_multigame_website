from django import template
from ..models import Rating

register = template.Library()


@register.simple_tag
def get_user_rating_value(post, user):
    """
    Возвращает значение рейтинга (1 или -1) для данного пользователя и поста.
    Возвращает пустую строку, если пользователь не голосовал или не аутентифицирован.
    """
    if not user.is_authenticated:
        return ''

    try:
        rating = Rating.objects.get(post=post, user=user)
        return rating.value
    except Rating.DoesNotExist:
        return ''