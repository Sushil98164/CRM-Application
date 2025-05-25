from django.db import models
from django.core.validators import EmailValidator
from utils.base_models import TimestampModel

class AboutUs(TimestampModel):
    heading=models.CharField(max_length=100)
    title=models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to='about_images', blank=True)

    def __str__(self):
        return "About Us"
    class Meta:
        verbose_name = 'about us'
        verbose_name_plural = 'about us'



class Service(TimestampModel):
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title
   
    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'


class Contact(TimestampModel):
    name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator(message="Enter a valid email address.")])
    subject = models.CharField(max_length=200)
    message = models.TextField()

    def __str__(self):
        return self.subject
    class Meta:
            verbose_name = 'Contact'
            verbose_name_plural = 'Contacts'


class FAQ(TimestampModel):
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        return self.question
    
    class Meta:
        verbose_name = "Frequently Asked Question"
        verbose_name_plural = "Frequently Asked Questions"
        

class OurClient(TimestampModel):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='clients/')

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Our clients"


class Testimonial(TimestampModel):
    text = models.TextField()
    client_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    image = models.ImageField(upload_to='testimonial_images')

    def __str__(self):
        return f'Testimonial by {self.client_name}'

    class Meta:
            verbose_name_plural = "Testimonials"

