# Generated by Django 5.0.1 on 2024-10-18 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_admin', '0019_comment_cause_of_incident_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='incident',
            name='incident_category',
            field=models.CharField(choices=[('Client incident', 'Client incident'), ('Transportation incident', 'Transportation incident'), ('Emergency incident', 'Emergency incident'), ('Near miss', 'Near miss'), ('Medication incident', 'Medication incident'), ('Behavioral incident', 'Behavioral incident'), ('Property damage', 'Property damage'), ('WHS (Workplace Health and Safety)', 'WHS (Workplace Health and Safety)'), ('Staff incident', 'Staff incident')], default='Client incident', max_length=255),
        ),
    ]
