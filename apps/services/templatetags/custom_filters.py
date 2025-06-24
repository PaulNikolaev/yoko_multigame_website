from django import template

register = template.Library()

@register.filter
def ru_pluralize(value, args):
    """
    Русское склонение слов по числу.
    """
    try:
        value = int(value)
        forms = [f.strip() for f in args.split(',')]
        if len(forms) != 3:
            raise ValueError("ru_pluralize filter requires 3 comma-separated forms.")

        if value % 10 == 1 and value % 100 != 11:
            return forms[0]
        elif (value % 10 >= 2) and (value % 10 <= 4) and (value % 100 < 10 or value % 100 >= 20):
            return forms[1]
        else:
            return forms[2]
    except (ValueError, IndexError):
        return args