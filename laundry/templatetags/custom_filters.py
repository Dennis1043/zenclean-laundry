from django import template

register = template.Library()

@register.filter
def sum_attribute(queryset, attribute):
    """Sum a list of objects by attribute"""
    total = 0
    for obj in queryset:
        total += getattr(obj, attribute, 0)
    return total
