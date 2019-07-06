from django import template

register = template.Library()


@register.filter(name='get_star_percentage')
def get_star_percentage(average_value):
    return (average_value / 5) * 111  # 111 is the 100% of the stars.css
