from django.db import models
from django.db.models import Case, When, Q, BooleanField, Value
from multiselectfield import MultiSelectField


class AssetManager(models.Manager):
    def get_queryset(self):
        """A QuerySet to add an annotation to specify if an Asset is complete or not"""
        return super().get_queryset().annotate(is_complete=Case(When(Q(
            Q(name__isnull=False),
            Q(department__isnull=False),
            Q(purpose__isnull=False),
            Q(owner__isnull=False),
            Q(private__isnull=False),
            Q(personal_data__isnull=False),
            Q(data_subject__isnull=False),
            Q(data_category__isnull=False),
            Q(Q(data_category__contains="others", data_category_others__isnull=False) |
              ~Q(data_category__contains="others")),
            Q(recipients_category__isnull=False),
            Q(retention__isnull=False),
            Q(retention_other__isnull=False),
            Q(storage_location__isnull=False),
            Q(storage_format__isnull=False),
            Q(Q(storage_format__contains="paper", paper_storage_security__isnull=False) |
              Q(storage_format__contains="digital", digital_storage_security__isnull=False))),
            then=Value(True)), default=Value(False), output_field=BooleanField()))


class Asset(models.Model):
    """"Model to store Assets for the Information Asset Register"""

    # a custom manager to include the annotation is_complete
    objects = AssetManager()

    # General - asset level
    name = models.CharField(max_length=255, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    purpose = models.CharField(max_length=255, null=True, blank=True)
    owner = models.CharField(max_length=50, null=True, blank=True)
    private = models.NullBooleanField(null=True, blank=True)

    # Persona Data
    personal_data = models.NullBooleanField(null=True, blank=True)
    DATA_SUBJECT_CHOICES = (
        ('students', 'Students, applicants'),
        ('staff', 'Staff, job applicants'),
        ('alumni', 'Alumni, supporters'),
        ('research', 'Research participants'),
        ('patients', 'Patients'),
        ('supplier', 'Suppliers, professional advisers and consultants'),
        ('public', 'Members of public'),
    )
    data_subject = MultiSelectField(choices=DATA_SUBJECT_CHOICES, null=True, blank=True)
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
    data_category = MultiSelectField(choices=DATA_CATEGORY_CHOICES, null=True, blank=True)
        # To be used when there data_category selected is "others"
    data_category_others = models.CharField(max_length=255, null=True, blank=True)
    recipients_category = models.CharField(max_length=255, null=True, blank=True)
    recipients_outside_eea = models.CharField(max_length=255, null=True, blank=True)
    RETENTION_CHOICES = (
        ('<=1', '1 year or less'),
        ('>1,<=5', '>1 to 5 years'),
        ('>5,<=10', '>5 to 10 years'),
        ('>10,<=75', '>10 to 75 years'),
        ('forever', 'Forever'),
        ('other', 'Other (please specify)'),
    )
    retention = models.CharField(max_length=255, choices=RETENTION_CHOICES, null=True, blank=True)
    retention_other = models.CharField(max_length=255, null=True, blank=True)

    # Risks
    RISK_CHOICES = (
        ('financial', 'Financial'),
        ('operational', 'Operational'),
        ('compliance', 'Compliance'),
        ('reputational', 'Reputational'),
        ('safety', 'Personal Safety'),
    )
    risk_type = MultiSelectField(choices=RISK_CHOICES, null=True, blank=True)

    # Storage
    storage_location = models.CharField(max_length=255, null=True, blank=True)
    STORAGE_FORMAT_CHOICES = (
        ('digital', 'Digital'),
        ('paper', 'Paper'),
    )
    storage_format = MultiSelectField(choices=STORAGE_FORMAT_CHOICES, null=True, blank=True)
        # Only if storage_format = 'paper'
    PAPER_STORAGE_SECURITY_CHOICES = (
        ('locked_cabinet', 'Locked filing cabinet'),
        ('safe', 'Safe'),
        ('locked_room', 'Locked room'),
        ('locked_building', 'Locked building'),
    )
    paper_storage_security = MultiSelectField(choices=PAPER_STORAGE_SECURITY_CHOICES,
                                              null=True, blank=True)
        # Only if storage_format = 'digital'
    DIGITAL_STORAGE_SECURITY_CHOICES = (
        ('pwd_controls', 'Password controls'),
        ('acl', 'Access control lists'),
        ('backup', 'Backup'),
        ('encryption', 'Encryption'),
    )
    digital_storage_security = MultiSelectField(choices=DIGITAL_STORAGE_SECURITY_CHOICES,
                                                null=True, blank=True)
