# Generated by Django 4.2.16 on 2025-02-28 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bellscrm_admin', '0007_alter_company_company_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='mandatory_incident_report_code',
        ),
        migrations.AlterField(
            model_name='company',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='companydetail',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='companydetail',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
