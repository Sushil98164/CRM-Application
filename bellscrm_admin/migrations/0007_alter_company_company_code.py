# Generated by Django 4.2.8 on 2024-01-06 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bellscrm_admin', '0006_company_is_deleted_companydetail_is_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='company_code',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
