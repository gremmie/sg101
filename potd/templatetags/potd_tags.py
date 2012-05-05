"""
Template tags for the POTD application. 
"""
from django import template
from potd.models import Current

register = template.Library()

@register.inclusion_tag('potd/potd_block.html')
def photo_of_the_day():
   potd = Current.objects.get_current_photo()
   return {
      'potd': potd,
   }
