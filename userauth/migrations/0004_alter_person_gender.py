# Generated by Django 4.2.8 on 2024-01-04 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0003_alter_person_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='Male', max_length=20),
            preserve_default=False,
        ),
    ]
