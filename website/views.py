from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from .models import *
from .forms import ContactForm
from django.contrib import messages
from website.utils import *
# from company_subscription.models import Plans
from django.urls import reverse
from django.http import HttpResponse



class LandingPage(View):
    def get_queryset(self, model):
        return model.objects.all()

    def get_context_data(self):
        context = {}
        context['clients'] = self.get_queryset(OurClient)
        context['about_us'] = AboutUs.objects.first()
        context['services'] = self.get_queryset(Service)
        context['faqs'] = self.get_queryset(FAQ)
        # context['plans'] = self.get_queryset(Plans)
        context['testimonials'] = self.get_queryset(Testimonial)
        context['form'] = ContactForm()
        return context

    # def get(self, request, *args, **kwargs):
    #     context = self.get_context_data()
    #     return render(request, "landing_website/index.html", context)
    
    def get(self, request, *args, **kwargs):
        current_host = request.get_host().lower()
        if current_host == "bellscrm.com.au" or current_host == "www.bellscrm.com.au":
            context = self.get_context_data()
            return render(request, "landing_website/index.html", context)
        else:
            return redirect(reverse('user_auth:login'))


    
class ContactPage(View):
    template = "landing_website/contact.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)

class AboutUsPage(View):
    template = "landing_website/about.html"

    def get(self, request, *args, **kwargs):
        about_us = AboutUs.objects.all()
        return render(request, self.template, {'about_us': about_us})


class SolutionPage(View):
    template = "landing_website/solutions.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)
    

class ContactView(View):
    template_name = 'landing_website/contact.html'
    form_class = ContactForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            name = form.cleaned_data['name']
            subject=form.cleaned_data['subject']
            message = form.cleaned_data['message']
            email=form.cleaned_data['email']
            contact_template = 'landing_website/email/contact-email.html'
            send_contact_email(name,subject,message,email,contact_template)
            messages.success(request, "Your message has been sent. Thank you!")
            landing_page_url = reverse('website:landing_page') + '#contact'  
            return redirect(landing_page_url)
        else:
            return render(request, 'landing_website/index.html', {'form': form,'is_from_contact':True})
        
   


class HealthCheckView(View):
    def get(self,request):
        return HttpResponse("Hi")