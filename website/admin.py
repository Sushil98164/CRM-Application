from django.contrib import admin
from .models import *
from ckeditor.widgets import CKEditorWidget
from django import forms



class AboutUsAdminForm(forms.ModelForm):
    class Meta:
        model = AboutUs
        fields = '__all__'
        widgets = {
            'content': CKEditorWidget(),
        }

class AboutUsAdmin(admin.ModelAdmin):
    form = AboutUsAdminForm
    list_display = ['id', 'title', 'content', 'image']



class ServiceAdminForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = '__all__'
        widgets = {
            'description': CKEditorWidget(),
        }


class ServiceAdmin(admin.ModelAdmin):
    form = ServiceAdminForm


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'message')
    
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'answer')


class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview')

    def image_preview(self, obj):
        return obj.image.url if obj.image else None
    image_preview.short_description = 'Image Preview'



class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('text', 'client_name', 'position')




admin.site.register(Testimonial, TestimonialAdmin)
admin.site.register(OurClient, ClientAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(AboutUs,AboutUsAdmin)
