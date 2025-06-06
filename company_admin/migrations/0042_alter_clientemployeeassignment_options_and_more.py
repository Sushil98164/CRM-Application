# Generated by Django 4.2.16 on 2025-02-28 09:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bellscrm_admin', '0008_remove_company_mandatory_incident_report_code_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('company_admin', '0041_departmentclientassignment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clientemployeeassignment',
            options={'permissions': [('update_all_services', 'Can update all services'), ('update_service_their_team_own', 'Can update services owned by their own team'), ('update_service_of_their_own', 'Can update their own services'), ('update_none', 'No permission to update services'), ('read_all_services', 'Can read all services'), ('read_service_their_team_own', 'Can read services owned by their own team')], 'verbose_name': 'Client Employee Assignment', 'verbose_name_plural': 'Client Employee Assignments'},
        ),
        migrations.AlterModelOptions(
            name='companytermsandconditionspolicy',
            options={'permissions': [('create_terms_and_conditions_all', 'Can create terms and conditions'), ('create_none_terms_and_conditions', 'No permission to create terms and conditions'), ('view_terms_and_conditions_all', 'Can view terms and conditions'), ('view_none_terms_and_conditions', 'No permission to view terms and conditions'), ('update_terms_and_conditions_all', 'Can Update terms and conditions'), ('update_none_terms_and_conditions', 'No permission to update terms and conditions'), ('create_privacy_policy_all', 'Can create privacy policy'), ('create_none_privacy_policy', 'No permission to create privacy policy'), ('view_privacy_policy_all', 'Can view privacy policy'), ('view_none_privacy_policy', 'No permission to view privacy policy'), ('update_privacy_policy_all', 'Can update privacy policy'), ('update_none_privacy_policy', 'No permission to update privacy policy')], 'verbose_name': 'Company Terms and Conditions Policy', 'verbose_name_plural': 'Company Terms and Conditions Policies'},
        ),
        migrations.AlterModelOptions(
            name='dailyshiftcasenote',
            options={'permissions': [('create_progress_notes_own', 'Can create progress notes for their own records'), ('create_progress_notes_no_access', 'No permission to create progress notes'), ('update_progress_notes_all', 'Can update all progress notes'), ('update_progress_notes_own_team', 'Can update progress notes for their own team'), ('update_progress_notes_own', 'Can update progress notes for their own records'), ('update_progress_notes_no_access', 'No permission to update progress notes'), ('view_progress_notes_all', 'Can view all progress notes'), ('view_progress_notes_own_team', 'Can view progress notes for their own team'), ('view_progress_notes_own', 'Can view progress notes for their own records'), ('view_progress_notes_no_access', 'No permission to view progress notes'), ('export_progress_notes_all', 'Can export all progress notes'), ('export_progress_notes_own_team', 'Can export progress notes for their own team'), ('export_none', 'No permission to export progress notes')], 'verbose_name': 'DailyShiftCaseNote', 'verbose_name_plural': 'DailyShiftCaseNotes'},
        ),
        migrations.AlterModelOptions(
            name='incident',
            options={'permissions': [('create_incident_all', 'Can create incidents for all teams'), ('create_incident_own_team', 'Can create incidents for their own team'), ('create_incident_there_own', 'Can create incidents for their own'), ('create_no_access_to_incidents', 'No permission to create incident'), ('tag_employee_in_incident_all', 'Can tag employees in incidents for all teams'), ('tag_employee_in_incident_own_team', 'Can tag employees in incidents for their own team'), ('review_incident_all', 'Can review incidents for all teams'), ('review_incident_own_team', 'Can review incidents for their own team'), ('view_incident_all', 'Can view incidents for all teams'), ('view_incident_own_team', 'Can view incidents for their own team'), ('view_incident_own', 'Can view their own incidents'), ('view_incident_no_access', 'No permission to view incidents'), ('update_tag_employee_in_incident_all', 'Can update employee tags in incidents for all teams'), ('update_tag_employee_in_incident_own_team', 'Can update employee tags in incidents for their own team'), ('update_incident_all', 'Can update incidents for all teams'), ('update_incident_own_team', 'Can update incidents for their own team'), ('update_incident_no_access', 'No permission to update incidents'), ('delete_incident_report_all', 'Can delete incident reports for all teams'), ('delete_incident_report_own_team', 'Can delete incident reports for their own team'), ('export_incident_report_all', 'Can export incident reports for all teams'), ('export_incident_report_own_team', 'Can export incident reports for their own team'), ('export_incident_no_access', 'No permission to export incident reports'), ('update_incident_investigation_all', 'Can update incident investigations for all teams'), ('update_incident_investigation_own_team', 'Can update incident investigations for their own team'), ('update_incident_investigation_none', 'No access to update incident investigations.'), ('read_incident_investigation_all', 'Can read incident investigations for all teams'), ('read_incident_investigation_own_team', 'Can read incident investigations for their own team'), ('read_incident_investigation_none', 'No access to read incident investigations.'), ('mark_incident_investigation_completed_all', 'Can mark incident investigations as completed for all teams'), ('mark_incident_investigation_completed_own_team', 'Can mark incident investigations as completed for their own team'), ('can_comment_on_incident_all', 'Can comment on incident investigations for all teams'), ('can_comment_on_incident_own_team', 'Can comment on incident investigations for their own team'), ('read_all_reports', 'Can read all reporting'), ('read_team_reports', 'Can read reporting for their own team'), ('read_own_reports', 'Can read reporting for their own records'), ('read_no_access_to_reports', 'No permission to read reporting'), ('create_hierarchy_all', 'Can create hierarchy for all teams'), ('create_none_hierarchy', 'No permission to create hierarchy'), ('update_hierarchy_all', 'Can update hierarchy for all teams'), ('update_none_hierarchy', 'No permission to update hierarchy'), ('read_hierarchy_all', 'Can read hierarchy for all teams'), ('read_none_hierarchy', 'No permission to read hierarchy')], 'verbose_name': 'Incident', 'verbose_name_plural': 'Incidents'},
        ),
        migrations.AlterModelOptions(
            name='riskassessment',
            options={'permissions': [('create_all_risk_assessments', 'Can create all risk assessments'), ('create_risk_assessments_team_own', 'Can create risk assessments for their own team'), ('create_risk_assessments_of_their_own', 'Can create their own risk assessments'), ('create_none', 'No permission to create risk assessments'), ('read_all_risk_assessments', 'Can read all risk assessments'), ('read_risk_assessments_team_own', 'Can read risk assessments for their own team'), ('read_risk_assessments_of_their_own', 'Can read their own risk assessments'), ('read_none', 'No permission to read risk assessments'), ('update_all_risk_assessments', 'Can update all risk assessments'), ('update_team_risk_assessments', 'Can update risk assessments for their own team'), ('update_own_risk_assessments', 'Can update their own risk assessments'), ('update_none', 'No permission to update risk assessments'), ('delete_all_risk_assessments', 'Can delete all risk assessments'), ('delete_risk_assessments_team_own', 'Can delete risk assessments for their own team'), ('authorize_risk_assessment_all', 'Can authorize risk assessments for all teams'), ('authorize_risk_assessment_own_team', 'Can authorize risk assessments for their own team'), ('review_risk_assessment_all', 'Can review risk assessments for all teams'), ('review_risk_assessment_own_team', 'Can review risk assessments for their own team')], 'verbose_name': 'Risk Assessment', 'verbose_name_plural': 'Risk Assessments'},
        ),
        migrations.AlterField(
            model_name='clientemployeeassignment',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='clientemployeeassignment',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='companytermsandconditionspolicy',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='companytermsandconditionspolicy',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='dailyshiftcasenote',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='dailyshiftcasenote',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='departmentclientassignment',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='departmentclientassignment',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='employeepolicyacknowledgment',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='employeepolicyacknowledgment',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='incident',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='incident',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='incidentattachment',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='incidentattachment',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='incidenttaggedemployee',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='incidenttaggedemployee',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='mandatoryincident',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='mandatoryincident',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='mandatoryincidentattachment',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='mandatoryincidentattachment',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskarea',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskarea',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskassessment',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskassessment',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskassessmentdetail',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskassessmentdetail',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskdocumentationapproval',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskdocumentationapproval',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskmonitercontrol',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='riskmonitercontrol',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='risktype',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='risktype',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='CompanyGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_by', models.CharField(blank=True, max_length=255, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=255, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company_groups', to='bellscrm_admin.company')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company_groups', to='auth.group')),
            ],
            options={
                'unique_together': {('group', 'company')},
            },
        ),
    ]
