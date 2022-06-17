from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})


@register.filter
def pluralize_ru(value, variants):
    value = abs(int(value))
    variants = variants.split(',')

    if (value % 10 == 1) and (value % 100 != 11):
        variant = 0
    elif ((value % 10 >= 2)
          and (value % 10 <= 4)
          and (value % 100 < 10 or value % 100 >= 20)):
        variant = 1
    else:
        variant = 2

    return variants[variant]
