# Generated by Django 2.0.1 on 2018-02-02 17:51

from django.db import migrations, models
import multiselectfield.db.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='data_category',
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True, choices=[('education', 'Education details'),
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
                                     ('criminal', 'Criminal proceedings, outcomes and sentences')],
                db_index=True, max_length=145, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='data_subject',
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True, choices=[('students', 'Students, applicants'),
                                     ('staff', 'Staff, job applicants'),
                                     ('alumni', 'Alumni, supporters'),
                                     ('research', 'Research participants'),
                                     ('patients', 'Patients'),
                                     ('supplier',
                                      'Suppliers, professional advisers and consultants'),
                                     ('public', 'Members of public')],
                db_index=True, max_length=55, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='department',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='digital_storage_security',
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True, choices=[('pwd_controls', 'Password controls'),
                                     ('acl', 'Access control lists'), ('backup', 'Backup'),
                                     ('encryption', 'Encryption')],
                db_index=True, max_length=34, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='id',
            field=models.UUIDField(db_index=True, default=uuid.uuid4,
                                   editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='asset',
            name='name',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='owner',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='paper_storage_security',
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True, choices=[('locked_cabinet', 'Locked filing cabinet'),
                                     ('safe', 'Safe'), ('locked_room', 'Locked room'),
                                     ('locked_building', 'Locked building')],
                db_index=True, max_length=47, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='personal_data',
            field=models.NullBooleanField(db_index=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='private',
            field=models.NullBooleanField(db_index=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='purpose',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='recipients_category',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='recipients_outside_eea',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='research',
            field=models.NullBooleanField(db_index=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='retention',
            field=models.CharField(
                blank=True, choices=[('<=1', '1 year or less'), ('>1,<=5', '>1 to 5 years'),
                                     ('>5,<=10', '>5 to 10 years'),
                                     ('>10,<=75', '>10 to 75 years'), ('forever', 'Forever'),
                                     ('other', 'Other (please specify)')],
                db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='retention_other',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='risk_type',
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True, choices=[('financial', 'Financial'), ('operational', 'Operational'),
                                     ('compliance', 'Compliance'),
                                     ('reputational', 'Reputational'),
                                     ('safety', 'Personal Safety')],
                db_index=True, max_length=52, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='storage_format',
            field=multiselectfield.db.fields.MultiSelectField(
                blank=True, choices=[('digital', 'Digital'), ('paper', 'Paper')],
                db_index=True, max_length=13, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='storage_location',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
    ]