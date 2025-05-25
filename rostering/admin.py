from django.contrib import admin
from rostering.models import Shifts

@admin.register(Shifts)
class ShiftsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'employee', 
        'client', 
        'company', 
        'start_date_time', 
        'end_date_time', 
        'shift_category', 
        'shift_type', 
        'status', 
        'total_hour',
        'is_deleted',
        'created_at'
    )
    list_filter = ('employee', 'client', 'company', 'shift_category', 'shift_type', 'status','is_deleted','created_at')
    raw_id_fields = ('employee', 'client', 'company')
    search_fields = ('employee__name', 'client__name', 'company__name', 'shift_category', 'shift_type', 'status')
    ordering = ('-start_date_time',)

