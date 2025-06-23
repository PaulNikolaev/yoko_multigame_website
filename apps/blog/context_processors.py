from .models import Category


def categories_processor(request):
    """
    Добавляет все категории в контекст для каждого запроса.
    """
    return {'categories': Category.objects.all()}
