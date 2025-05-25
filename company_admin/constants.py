
CHOICES_INCIDENT_REOPORTS = (
    ('New','New'),
    ('InProgress','InProgress'),
    ('Closed','Closed'),
)

TYPE_OF_INCIDENT_REPORT = (
    ('Incident','Incident'),
    ('Mandatory Incident','Mandatory Incident')
)

TYPE_OF_SEVERITY_LEVEL=(
    ('Not applicable','Not applicable'),
    ('Harmful to self','Harmful to self'),
    ('Harmful to property','Harmful to property'),
    ('Harmful to others','Harmful to others')
)




SEVERITY_LEVEL_CHOICES = {
    'Harmful to self': sorted([
        ('L1', 'No first aid/treatment required'),
        ('L2', 'Minor injury, requiring some first aid (e.g. creams, band aids etc.)'),
        ('L3', 'Resulting in no obvious serious injury but may cause long lasting injury. E.g. head banging, serious anal picking etc.'),
        ('L4', 'Treatment by doctor or ambulance required'),
    ], key=lambda x:x[1]),
    'Harmful to property': [
        ('L1', 'Damage to property less than $50'),
        ('L2', 'Damage $50-$100'),
        ('L3', 'Damage > $150'),
    ],
    'Harmful to others': sorted([
        ('L1', 'Shouts/swears up to 20 mins / verbal or physical threat'),
        ('L2', 'Hit/kick/pushing - not causing bruising or other injury / shouts more than 20 mins'),
        ('L3', 'Hit/kick/pushing - causing minor first aid'),
        ('L4', 'Treatment by doctor of ambulance required for either client or staff / staff refuse to work with client or are removed from shift cycle'),
    ], key=lambda x:x[1]),
}

INCIDENT_CATEGORY_CHOICES = [
    ('Injury', 'Injury'),
    ('Sexual or Physical assault', 'Sexual or Physical assault'),
    ('Death', 'Death'),
    ('Abuse or neglect', 'Abuse or neglect'),
    ('Unauthorized use of restrictive practice', 'Unauthorized use of restrictive practice'),
    ('Waste incident', 'Waste incident'),
    ('Medication incident', 'Medication incident'),
    ('Client behaviour of concern', 'Client behaviour of concern'),
    ('Client illness', 'Client illness'),
    ('Work health and safety', 'Work health and safety'),
    ('Near miss', 'Near miss'),
    ('Other', 'Other'),
]

EMPLOYEE_INVOLVED = [
    ('yes', 'Yes'),
    ('no', 'No'),
]

INCIDENT_CLASSIFICATION_CHOICES = [
    ('Catastrophic', 'Catastrophic'),
    ('Major', 'Major'),
    ('Moderate', 'Moderate'),
    ('Minor', 'Minor'),
    ('Insignificant', 'Insignificant'),
]



POLICY_CHOICES = [
    ('terms_and_conditions', 'Terms and Conditions'),
    ('privacy_policy', 'Privacy Policy'),
]



RISK_CATEGORY = (
    ('High','High'),
    ('Medium','Medium'),
    ('Low','Low'),
)


TRUE_FALSE_CHOICES = (
    (True, 'Yes'),
    (False, 'No')
)

YES_NO_CHOICE = (
    (1, 'Yes'),
    (0, 'No')
)

CHOICES_GENDER = (
    ("Male", "Male"),
    ("Female", "Female"),
    ("Other", "Other"),
)

CHOICES_FUND_MANAGEMENT = (
    ('Self Managed', 'Self Managed'),
    ('Agency Managed', 'Agency Managed'),
    ('Plan Managed', 'Plan Managed'),
)


CHOICE_ROLES = (
    (1, 'Admin'),
    (2, 'Manager'),
    (3, 'Employee'),
)

CHOICES_INVESTIGATION_HIERARCHY = (
    ("incident_investigation_hierarchy", "Incident Investigation Hierarchy"),
)

STAGE_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
    )