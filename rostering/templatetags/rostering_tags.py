from django import template
register = template.Library()




@register.simple_tag
def get_proper_counter(forloop_counter, page_obj):
    """
    Calculate the proper counter number based on pagination
    
    Args:
        forloop_counter: The current forloop.counter value
        page_obj: The page object from Django's pagination
        
    Returns:
        int: The calculated counter number
    """
    items_per_page = page_obj.paginator.per_page
    current_page = page_obj.number
    return (current_page - 1) * items_per_page + forloop_counter