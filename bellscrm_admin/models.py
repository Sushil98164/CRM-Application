from django.db import models
from django.db.models import Max
from django.contrib.sites.models import Site
from utils.base_models import TimestampModel
from userauth.utils import BellsManager
from utils.default_template_permissions import assign_permissions_to_groups

class Company(TimestampModel):
    name=models.CharField(max_length=150)
    address=models.TextField(null=True,blank=True)
    contact=models.CharField(max_length=20,null=True,blank=True)
    company_code = models.CharField(max_length=50, unique=True)
    client_code=models.CharField(max_length=50,null=True, blank=True)
    incident_report_code=models.CharField(max_length=50,null=True, blank=True)
    # mandatory_incident_report_code=models.CharField(max_length=50,null=True, blank=True)
    employee_code=models.CharField(max_length=50,null=True, blank=True)
    register_url = models.URLField(max_length=250,unique=True,null=True, blank=True)
    login_url = models.URLField(max_length=250,unique=True,null=True, blank=True)
    email_for_alerts = models.EmailField(max_length=250,null=True, blank=True)
    objects = models.Manager()  
    bells_manager = BellsManager()  

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        
    def mandatory_next_sno(self):
        sno = 1
        try:
            last_incident = self.incidents.filter(report_type="Mandatory Incident").aggregate(Max('sno'))['sno__max']
            if last_incident is not None:
                sno = last_incident + 1
        except Exception as e:
            pass
        return sno

    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            assign_permissions_to_groups(self)
            
        current_site = Site.objects.get_current()
        if current_site.domain in ['localhost', '127.0.0.1']:
            protocol = "http"
            port = ":8000"
        else:
            protocol = "https"
            port = ""
        self.register_url = f"{protocol}://{self.company_code}.{current_site.domain}{port}/register/"
        self.login_url = f"{protocol}://{self.company_code}.{current_site.domain}{port}/login/"
        super().save(*args, **kwargs)
        
    def next_sno(self):
        sno = 1
        try:
            last_incident = self.incidents.filter(report_type="Incident").aggregate(Max('sno'))['sno__max']
            if last_incident is not None:
                sno = last_incident + 1
            while self.incidents.filter(sno=sno).exists():
                sno += 1 
        except Exception as e:
            print(e)
            pass
        return sno
    
    def next_daily_shift_sno(self):
        sno = 1
        try:
            last_daily_shift = self.daily_shift_case_notes.aggregate(Max('sno'))['sno__max']

            if last_daily_shift:
                sno = last_daily_shift + 1
            while self.daily_shift_case_notes.filter(sno=sno).exists():
                sno += 1 
        except Exception as e:
            print(e)
            pass
        return sno
    
    def mandatory_report_code(self):
        return f"{self.mandatory_incident_report_code}{self.mandatory_next_sno():04}"

    def next_incident_report_code(self):
        return f"{self.incident_report_code}{self.next_sno():04}"


    def __str__(self):
        return f"{self.name}"

class CompanyDetail(TimestampModel):
    company= models.OneToOneField(Company, on_delete=models.CASCADE, related_name="company_detail")
    company_code = models.CharField(max_length=50, null=True, blank=True)
    client_code=models.CharField(max_length=50,null=True, blank=True)
    incident_report_code=models.CharField(max_length=50,null=True, blank=True)
    employee_code=models.CharField(max_length=50,null=True, blank=True)
    

    class Meta:
        verbose_name = 'CompanyDetail'
        verbose_name_plural = 'CompanyDetails'

    def __str__(self):
        return f"{self.company}"



