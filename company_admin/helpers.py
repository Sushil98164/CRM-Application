from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

def paginate_query(queryset, page, items_per_page):
    
    paginator = Paginator(queryset, items_per_page)
    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data = paginator.page(paginator.num_pages)

    total_entries = paginator.count
    if total_entries > 0:
        start_entry = ((paginated_data.number - 1) * items_per_page) + 1
        end_entry = min(start_entry + items_per_page - 1, total_entries)
    else:
        start_entry = 0
        end_entry = 0

        

    return {
        'paginated_data': paginated_data,
        'start_entry': start_entry,
        'end_entry': end_entry,
        'total_entries': total_entries,
    }







































































































































































































