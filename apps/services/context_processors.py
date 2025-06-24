from apps.blog.models import Category
from apps.accounts.models import Profile
from django.contrib.auth.models import User
import datetime


def categories_processor(request):
    """
    Добавляет все категории в контекст для каждого запроса.
    """
    return {'categories': Category.objects.all()}


def data_processor(request):
    """
    Добавляет подсчет количества пользователей, стран и городов, где они проживают,
    а также текущий год.
    """
    total_users = User.objects.count()
    unique_cities_count = Profile.objects.filter(city__isnull=False).exclude(city__exact='').values(
        'city').distinct().count()
    unique_countries_count = Profile.objects.filter(country__isnull=False).exclude(country__exact='').values(
        'country').distinct().count()

    return {
        'total_users_count': total_users,
        'unique_cities_count': unique_cities_count,
        'unique_countries_count': unique_countries_count,
        'current_year': datetime.datetime.now().year,  # Добавлено
    }
