# Generated by Django 4.2.8 on 2024-05-27 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company_admin', '0008_alter_incident_injured_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='incident',
            name='action_taken_for_individual',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='incident',
            name='post_incident_details',
            field=models.TextField(blank=True, null=True),
        ),
    ]
