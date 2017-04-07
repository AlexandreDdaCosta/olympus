import re

from django import template

register = template.Library()

@register.filter
def concatenate(arg1,arg2):
    return str(arg1) + str(arg2)

@register.filter()
def secure_url(string):
	return re.sub(r'http://', r'https://', string, flags=re.MULTILINE)

@register.filter()
def underscore_to_space(string):
	return re.sub('_', ' ', string)
