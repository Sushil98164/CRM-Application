from django.db import models
from userauth.models import TimestampModel,Employee,Client,Company
from rostering.constants import *
from userauth.utils import BellsManager
from utils.model_permissions import SHIFT_PERMISSIONS
    

class Shifts(TimestampModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name = "shifts")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name = "shifts")
    company= models.ForeignKey(Company, on_delete=models.CASCADE, related_name = "shifts")
    author = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name = "shifts_author")
    start_date_time = models.DateTimeField()
    end_date_time = models.DateTimeField()
    shift_category= models.CharField(max_length = 100, choices=CHOICES_SHIFT_CATEGORY, default="Regular shift")
    shift_type = models.CharField(max_length = 100, choices=CHOICES_SHIFT_TYPE)
    status = models.CharField(max_length = 100, choices=CHOICES_SHIFT_STATUS, default="Draft")
    total_hour = models.CharField(max_length=50,null=True,blank=True)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()  # Our custom manager.
    
    class Meta:
        verbose_name = 'Shift'
        verbose_name_plural = 'Shifts'
        
        permissions = SHIFT_PERMISSIONS

    def __str__(self):
        return f"{self.employee} - {self.client}"
    
    def calculate_total_hour(self, start_date_time, end_date_time):
        if start_date_time and end_date_time:
            time_difference = end_date_time - start_date_time
            total_seconds = time_difference.total_seconds()
            total_hours = total_seconds // 3600 
            minutes = (total_seconds % 3600) // 60
            return f"{int(total_hours)} hours and {int(minutes)} minutes"
        return None