from django.db import models
from userauth.models import Employee, TimestampModel, Client
from userauth.utils import BellsManager
from utils.model_permissions import DOCUMENT_PERMISSIONS  



DOCUMENTS_STATUS = (
    ('Pending','Pending'),
    ('Reject','Reject'),
    ('Approved','Approved')

)


class IDsAndChecksDocuments(TimestampModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='documents/IDsandChecks',null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True) 
    status = models.CharField(max_length = 100, choices=DOCUMENTS_STATUS,default="Pending")
    objects = models.Manager()  
    bells_manager = BellsManager() 

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "IDs and Checks Document"
        verbose_name_plural = "IDs and Checks Documents"
        
        permissions = DOCUMENT_PERMISSIONS
    


class QualificationDocuments(TimestampModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='documents/Qualification',null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True) 
    status = models.CharField(max_length = 100, choices=DOCUMENTS_STATUS,default="Pending")
    objects = models.Manager() 
    bells_manager = BellsManager()  
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Qualification Document"
        verbose_name_plural = "Qualification Documents"
    

class OtherDocuments(TimestampModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='documents/Other',null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True) 
    status = models.CharField(max_length = 100, choices=DOCUMENTS_STATUS,default="Pending")
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()  # Our custom manager.
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Other Document"
        verbose_name_plural = "Other Documents"



    
    
class ClientAssignment(TimestampModel):
    clients = models.ManyToManyField(Client, through='ClientAssignmentDetail', related_name='client_assignments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="client_assignments")  # Changed to OneToOneField
    assigned_date = models.DateField(auto_now_add=True, verbose_name="Assigned Date")
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()  # Our custom manager.
    class Meta:
        verbose_name = "Client Assignment"
        verbose_name_plural = "Client Assignments"
    
    def __str__(self):
        return f"Assignment for {self.employee} on {self.assigned_date}"


class ClientAssignmentDetail(TimestampModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="client_assignments_detail", verbose_name="client")
    client_assignment = models.ForeignKey(ClientAssignment, on_delete=models.CASCADE, related_name='client_assignment_details')
    is_deleted = models.BooleanField(default=False)
    objects = models.Manager()  # The default manager.
    bells_manager = BellsManager()  # Our custom manager.

    class Meta:
        verbose_name = "Client Assignment Detail"
        verbose_name_plural = "Client Assignment Details"
    
    def __str__(self):
        return f"{self.client} in assignment {self.client_assignment}"
