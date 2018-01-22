from django.db import models
from multiselectfield import MultiSelectField


class Asset(models.Model):
    # General - asset level
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    purpose = models.CharField(max_length=255)
    owner = models.CharField(max_length=50)
    private = models.BooleanField()

    # Persona Data
    personal_data = models.BooleanField()
    DATA_SUBJECT_CHOICES = (
        ('students', 'Students, applicants'),
        ('staff', 'Staff, job applicants'),
        ('alumni', 'Alumni, supporters'),
        ('research', 'Research participants'),
        ('patients', 'Patients'),
        ('supplier', 'Suppliers, professional advisers and consultants'),
        ('public', 'Members of public'),
    )
    data_subject = MultiSelectField(choices=DATA_SUBJECT_CHOICES)
    DATA_CATEGORY_CHOICES = (
        ('personal', 'Personal details'),
        ('education', 'Education details'),
        ('employment', 'Employment details'),
        ('financial', 'Financial details'),
        ('social', 'Lifestyle and social circumstances'),
        ('visual', 'Visual images'),
        ('research', 'Research data'),
        ('medical', 'Medical records'),
        ('children', 'Personal data about children under 16'),
        ('racial', 'Racial or ethic origin'),
        ('political', 'Political opinions'),
        ('unions', 'Trade union membership'),
        ('religious', 'Religious or similar beliefs'),
        ('health', 'Physical or mental health details'),
        ('sexual', 'Sexual life and orientation'),
        ('genetic', 'Genetic information'),
        ('biometric', 'Biometric information'),
        ('criminal', 'Criminal proceedings, outcomes and sentences'),
        ('others', 'Other (please specify)'),
    )
    data_category = MultiSelectField(choices=DATA_CATEGORY_CHOICES)
        # To be used when there data_category selected is "others"
    data_category_others = models.CharField(max_length=255)
    recipients_category = models.CharField(max_length=255)
    recipients_outside_eea = models.BooleanField()
        # To be used when there data_category selected is "true"
    recipients_outside_eea_who = models.CharField(max_length=255)
    RETENTION_CHOICES = (
        ('<=1', '1 year or less'),
        ('>1,<=5', '>1 to 5 years'),
        ('>5,<=10', '>5 to 10 years'),
        ('>10,<=75', '>10 to 75 years'),
        ('forever', 'Forever'),
        ('other', 'Other (please specify)'),
    )
    retention = models.CharField(max_length=255, choices=RETENTION_CHOICES)
    retention_other = models.CharField(max_length=255)

    # Risks
    RISK_CHOICES = (
        ('financial', 'Financial'),
        ('operational', 'Operational'),
        ('compliance', 'Compliance'),
        ('reputational', 'Reputational'),
        ('safety', 'Personal Safety'),
    )
    risk_type = MultiSelectField(choices=RISK_CHOICES)

    # Storage
    storage_location = models.CharField(max_length=255)
    STORAGE_FORMAT_CHOICES = (
        ('digital', 'Digital'),
        ('paper', 'Paper'),
    )
    storage_format = MultiSelectField(choices=STORAGE_FORMAT_CHOICES)
        # Only if storage_format = 'paper'
    PAPER_STORAGE_SECURITY_CHOICES = (
        ('locked_cabinet', 'Locked filing cabinet'),
        ('safe', 'Safe'),
        ('locked_room', 'Locked room'),
        ('locked_building', 'Locked building'),
    )
    paper_storage_security = MultiSelectField(choices=PAPER_STORAGE_SECURITY_CHOICES)
        # Only if storage_format = 'digital'
    DIGITAL_STORAGE_SECURITY_CHOICES = (
        ('pwd_controls', 'Password controls'),
        ('acl', 'Access control lists'),
        ('backup', 'Backup'),
        ('encryption', 'Encryption'),
    )
    digital_storage_security = MultiSelectField(choices=DIGITAL_STORAGE_SECURITY_CHOICES)
