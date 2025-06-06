# Generated by Django 5.0.1 on 2024-11-26 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_admin', '0028_alter_companytermsandconditionspolicy_company_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companytermsandconditionspolicy',
            name='type',
            field=models.CharField(choices=[('privacy_policy', 'privacy_policy'), ('terms_and_conditions', 'terms_and_conditions')], max_length=255),
        ),
        migrations.AlterField(
            model_name='incident',
            name='incident_category',
            field=models.CharField(blank=True, choices=[('Medication incident', 'Medication incident'), ('Work health and safety', 'Work health and safety'), ('Waste incident', 'Waste incident'), ('Near miss', 'Near miss'), ('Injury', 'Injury'), ('Client behaviour of concern', 'Client behaviour of concern'), ('Death', 'Death'), ('Abuse or neglect', 'Abuse or neglect'), ('Other', 'Other'), ('Unauthorized use of restrictive practice', 'Unauthorized use of restrictive practice'), ('Client illness', 'Client illness'), ('Sexual or Physical assault', 'Sexual or Physical assault')], max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='incident',
            name='incident_classification',
            field=models.CharField(blank=True, choices=[('Catastrophic', 'Catastrophic'), ('Insignificant', 'Insignificant'), ('Minor', 'Minor'), ('Moderate', 'Moderate'), ('Major', 'Major')], max_length=255, null=True),
        ),
    ]
