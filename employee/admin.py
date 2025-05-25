from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from bellscrm_admin.models import Company
from .models import (
    IDsAndChecksDocuments,
    QualificationDocuments,
    OtherDocuments,
    ClientAssignment,
    ClientAssignmentDetail
)


class CompanyFilter(admin.SimpleListFilter):
    title = _('Company')
    parameter_name = 'company'

    def lookups(self, request, model_admin):
        companies = Company.objects.all()
        return [(company.id, company.name) for company in companies]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(employee__company_id=self.value())
        return queryset
    
@admin.register(IDsAndChecksDocuments)
class IDsAndChecksDocumentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'employee', 'expiry_date', 'file_link','is_deleted','created_at')
    list_filter = (CompanyFilter,'employee','status', 'expiry_date','is_deleted','created_at')
    raw_id_fields = ('employee',)

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}">Download</a>', obj.file.url)
        return "No file"


@admin.register(QualificationDocuments)
class QualificationDocumentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'employee', 'expiry_date', 'file_link','is_deleted','created_at')
    list_filter = (CompanyFilter,'employee','status', 'expiry_date','is_deleted','created_at')
    raw_id_fields = ('employee',)

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}">Download</a>', obj.file.url)
        return "No file"


@admin.register(OtherDocuments)
class OtherDocumentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'employee', 'expiry_date', 'file_link','is_deleted','created_at')
    list_filter = (CompanyFilter,'employee','status', 'expiry_date','is_deleted','created_at')
    raw_id_fields = ('employee',)

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}">Download</a>', obj.file.url)
        return "No file"


class ClientAssignmentDetailInline(admin.TabularInline):
    model = ClientAssignmentDetail
    extra = 0
    readonly_fields = ('client',)



@admin.register(ClientAssignment)
class ClientAssignmentAdmin(admin.ModelAdmin):
    inlines = [ClientAssignmentDetailInline]
    list_display = ('id', 'employee', 'assigned_date', 'clients_display')
    list_filter = ('employee','assigned_date',)
    readonly_fields = ('employee','assigned_date',)
    raw_id_fields = ('employee',)

    def clients_display(self, obj):
        active_clients = ClientAssignmentDetail.objects.filter(client_assignment=obj, is_deleted=False)
        return ", ".join([detail.client.person.first_name for detail in active_clients])

    clients_display.short_description = 'Clients'


@admin.register(ClientAssignmentDetail)
class ClientAssignmentDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'client_assignment', 'is_deleted')
    list_filter = ('is_deleted',)
    readonly_fields = ('client', 'client_assignment')
    raw_id_fields = ('client', 'client_assignment')

