import uuid
from automationcommon.models import ModelChangeMixin
from django.db import models
from django.db.models import Case, When, Q, BooleanField, Value
from multiselectfield import MultiSelectField


class AssetManager(models.Manager):
    """Custom :py:class:`models.Manager` sub class which adds an :py:attr:`is_complete`
    annotation to the :py:class:`~.Asset` instances in the query set. The :py:attr:`is_complete`
    annotation reflects whether the asset record is "complete" as defined in the requirements."""
    def get_queryset(self):
        """A QuerySet to add an annotation to specify if an Asset is complete or not"""
        return self.get_base_queryset().annotate(is_complete=Case(When(Q(
            Q(name__isnull=False),
            Q(department__isnull=False),
            Q(purpose__isnull=False),
            Q(Q(purpose='research', owner__isnull=False) |
              ~Q(purpose='research')),
            Q(Q(purpose='other', purpose_other__isnull=False) |
              ~Q(purpose='other')),
            Q(Q(personal_data=False) |
              Q(Q(personal_data=True), ~Q(data_subject=[]), ~Q(data_category=[]),
                recipients_outside_uni__isnull=False, recipients_outside_eea__isnull=False,
                retention__isnull=False)),
            Q(Q(recipients_outside_uni='yes', recipients_outside_uni_description__isnull=False) |
              ~Q(recipients_outside_uni='yes')),
            Q(Q(recipients_outside_eea='yes', recipients_outside_eea_description__isnull=False) |
              ~Q(recipients_outside_eea='yes')),
            ~Q(risk_type=[]),
            Q(storage_location__isnull=False),
            ~Q(storage_format=[]),
            Q(~Q(storage_format__contains='paper') |
              Q(Q(storage_format__contains='paper'), ~Q(paper_storage_security=[]))),
            Q(~Q(storage_format__contains='digital') |
              Q(Q(storage_format__contains='digital'), ~Q(digital_storage_security=[])))),
            then=Value(True)), default=Value(False), output_field=BooleanField()))

    def get_base_queryset(self):
        """
        Return the original un-annotated queryset. Useful when the is_complete annotation is not
        required.

        """
        return super().get_queryset()


class Asset(ModelChangeMixin, models.Model):

    def audit_compare(self, field, old, new):
        """
        Overridden as the base implementation doesn't correctly detect differences for
        MultiSelectField fields.

        :param field: The field being compared
        :param old: the original value
        :param new: the updated value
        :return: whether or not a change has been detected
        """
        if isinstance(field, MultiSelectField):
            return len(set(old if old else []) ^ set(new if new else [])) != 0
        return super(Asset, self).audit_compare(field, old, new)

    """"Model to store Assets for the Information Asset Register"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    # a custom manager to include the annotation is_complete
    objects = AssetManager()

    # General - asset level
    name = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    # TODO when issues with import data have been resolved this should be required
    department = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    PURPOSE_CHOICES = (
        ('teaching', 'Teaching'),
        ('research', 'Research (Academic)'),
        ('research_organisational', 'Research (Organisational)'),
        ('student_administration', 'Student administration'),
        ('staff_administration', 'Staff administration (HR)'),
        ('alumni_supporter_administration', 'Alumni/supporter administration'),
        ('supplier_customer_administration', 'Supplier/customer administration'),
        ('financial_estate_administration', 'Financial/estate administration'),
        ('governance_compliance', 'Governance/compliance'),
        ('security', 'Security'),
        ('marketing', 'Marketing'),
        ('public_engagement', 'Public engagement'),
        ('other', 'Other'),
    )
    purpose = models.CharField(max_length=255, choices=PURPOSE_CHOICES, null=True, blank=True,
                               db_index=True)
    purpose_other = models.TextField(null=True, blank=True, db_index=True)
    owner = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    private = models.BooleanField(default=False, db_index=True)

    # Persona Data
    personal_data = models.NullBooleanField(null=True, blank=True, db_index=True)
    DATA_SUBJECT_CHOICES = (
        ('students', 'Students, applicants'),
        ('staff', 'Staff, job applicants'),
        ('alumni', 'Alumni, supporters'),
        ('research', 'Research participants'),
        ('patients', 'Patients'),
        ('supplier', 'Suppliers, professional advisers and consultants'),
        ('public', 'Members of public'),
    )
    data_subject = MultiSelectField(choices=DATA_SUBJECT_CHOICES, null=True, blank=True,
                                    db_index=True)
    DATA_CATEGORY_CHOICES = (
        ('education', 'Education records'),
        ('alumni', 'Alumni records'),
        ('contact', 'Basic contact details'),
        ('employment', 'Employment records'),
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
    )
    data_category = MultiSelectField(choices=DATA_CATEGORY_CHOICES, null=True, blank=True,
                                     db_index=True)

    RECIPIENTS_OUTSIDE_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_sure', 'Not Sure'),
    )
    recipients_outside_uni = models.CharField(max_length=8, choices=RECIPIENTS_OUTSIDE_CHOICES,
                                              null=True, blank=True, db_index=True)
    recipients_outside_eea = models.CharField(max_length=8, choices=RECIPIENTS_OUTSIDE_CHOICES,
                                              null=True, blank=True, db_index=True)

    recipients_outside_uni_description = models.CharField(max_length=255, null=True, blank=True,
                                                          db_index=True)
    recipients_outside_eea_description = models.CharField(max_length=255, null=True, blank=True,
                                                          db_index=True)

    RETENTION_CHOICES = (
        ('<1', 'Less than 1 year'),
        ('>=1,<=5', '1 to 5 years'),
        ('>5,<=10', '5 to 10 years'),
        ('>10,<=75', '10 to 75 years'),
        ('forever', 'Forever'),
    )
    retention = models.CharField(max_length=255, choices=RETENTION_CHOICES, null=True, blank=True,
                                 db_index=True)

    # Risks
    RISK_CHOICES = (
        ('financial', 'Financial'),
        ('operational', 'Operational'),
        ('compliance', 'Compliance'),
        ('reputational', 'Reputational'),
        ('safety', 'Personal Safety'),
        ('none', 'None of the above'),
    )
    risk_type = MultiSelectField(choices=RISK_CHOICES, null=True, blank=True, db_index=True)
    risk_type_additional = models.TextField(null=True, blank=True, db_index=True)

    # Storage
    storage_location = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    STORAGE_FORMAT_CHOICES = (
        ('digital', 'Digital'),
        ('paper', 'Paper'),
    )
    storage_format = MultiSelectField(choices=STORAGE_FORMAT_CHOICES, null=True, blank=True,
                                      db_index=True)
    # Storage # Only if storage_format = 'paper'
    PAPER_STORAGE_SECURITY_CHOICES = (
        ('locked_cabinet', 'Locked filing cabinet'),
        ('safe', 'Safe'),
        ('locked_room', 'Locked room'),
        ('locked_building', 'Locked building'),
        ('none', 'None of the above'),
    )
    paper_storage_security = MultiSelectField(choices=PAPER_STORAGE_SECURITY_CHOICES,
                                              null=True, blank=True, db_index=True)
    # Storage # Only if storage_format = 'digital'
    DIGITAL_STORAGE_SECURITY_CHOICES = (
        ('pwd_controls', 'Password controls'),
        ('acl', 'Access control lists'),
        ('backup', 'Backup'),
        ('encryption', 'Encryption'),
        ('none', 'None of the above'),
    )
    digital_storage_security = MultiSelectField(choices=DIGITAL_STORAGE_SECURITY_CHOICES,
                                                null=True, blank=True, db_index=True)

    # Asset logs
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    deleted_at = models.DateTimeField(default=None, blank=True, null=True)
