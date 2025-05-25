from django.contrib import admin
from .models import *


class CompanyAdmin(admin.ModelAdmin):
    model = Company
    list_display = ['id','name','address','contact','register_url','login_url']
    exclude = ['created_by', 'updated_by']
admin.site.register(Company,CompanyAdmin)



class CompanyDetailsAdmin(admin.ModelAdmin):
    model = CompanyDetail
    list_display = ['id','client_code','employee_code','company_code','company']
admin.site.register(CompanyDetail,CompanyDetailsAdmin)