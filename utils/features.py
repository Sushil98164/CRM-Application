from enum import Enum
from enum import Enum

class Action(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    IMPORT = "import"
    READ = "read"
    VIEW = "view"  
    EXPORT = "export"  

class AccessLevel(Enum):

    # Dashboard access levels
    ALL_REPORTS = "All reportings"
    TEAM_REPORTS = "Reporting their team owns"
    OWN_REPORTS = "Reportings of their own"

    # Employee management access levels
    ALL_EMPLOYEES = "All employees"
    NONE = "None"
    TEAM_EMPLOYEES = "Employees their team owns"
    OWN_EMPLOYEES = "Self"
    ALL_DOCUMENTS = "All documents"
    TEAM_DOCUMENTS = "Documents their team owns"
    OWN_DOCUMENTS = "Document of their own"
    ALL_ACKNOWLEDGEMENTS = "All acknowledgements"
    TEAM_ACKNOWLEDGEMENTS = "Acknowledgements their team owns"

    # Client management access levels
    ALL_CLIENTS = "All clients"
    TEAM_CLIENTS = "Clients their team owns"
    OWN_CLIENTS = "Clients of their owns"
    ALL_RISK_ASSESSMENTS = "All risk assessments"
    TEAM_RISK_ASSESSMENTS = "Risk assessments their team owns"
    OWN_RISK_ASSESSMENTS = "Risk assessments of their own"

    # Department management access levels
    ALL_DEPARTMENTS = "All teams"
    TEAM_DEPARTMENTS = "Teams they own"

    # Shift management access levels
    ALL_SHIFTS = "All shifts"
    TEAM_SHIFTS = "Shifts their team owns"
    OWN_SHIFTS = "Shifts of their own"
    
    # Shift report access levels
    ALL_SHIFT_REPORTS = "All shift reports"
    TEAM_SHIFT_REPORTS = "Shift reports their team owns"
    
    # Roster management access levels
    ALL_ROSTERS = "All rosters"
    TEAM_ROSTERS = "Rosters their team owns"
    OWN_ROSTERS = "Rosters of their own"


    # Client Incident Report access levels
    ALL_CLIENT_INCIDENT_REPORT = "All Incidents"
    TEAM_CLIENT_INCIDENT_REPORT = "Incidents their team owns"
    OWN_CLIENT_INCIDENT_REPORT = "Incidents they own"


    # Service Delivery Team access levels
    ALL_SERVICES = "All services"
    TEAM_SERVICES = "Services their team owns"
    OWN_SERVICES = "Services of their own"

    # Progress Notes and Timesheet access levels
    ALL_PROGRESS_NOTES = "All progress notes"
    TEAM_PROGRESS_NOTES = "Progress notes their team owns"
    OWN_PROGRESS_NOTES = "Progress notes of their own"

    # Admin Control access levels
    ALL_INCIDENT_INVESTIGATIONS= "All investigations"
    TEAM_INCIDENT_INVESTIGATIONS = "Investigations their team owns"
    SELF_INCIDENT_INVESTIGATIONS= "Incident they own"

    ALL_RISK_INVESTIGATIONS = "All risk investigations"
    TEAM_RISK_INVESTIGATIONS = "Risk investigations their team owns"

    # settings access levels
    ALL_TERMS_AND_CONDITONS = "All terms and conditions"    
    ALL_PRIVACY_POLICY = "All privacy policy"
    ALL_HIERARCHY = "All hierarchy"
    ALL_PERMISSION = "All users"
    TEAM_PERMISSION = "Permission their team owns"
    OWN_PERMISSION = "Permission they own"
    


from utils.permission_sets import *
    
DEFAULT_FEATURE_DICT = {
    "dashboard": {
        "features": {
            "reportings": {
                "id":1,
                "name":"Reportings",
                "description": "Offers a comprehensive summary of incident reports for better decision-making.",
                "actions": [
                    {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_REPORTS.value, "code": "read_all_reports"},
                            {"name": AccessLevel.TEAM_REPORTS.value, "code": "read_team_reports"},
                            {"name": AccessLevel.OWN_REPORTS.value, "code": "read_own_reports"},
                            {"name": AccessLevel.NONE.value, "code": "read_no_access_to_reports"}
                        ],
                        "description": "Summary of Incident reports"
                    },
                ]
            },
        }
    },
    "employee_management": {
        "features": {
            "employee_profile": {
                "id":2,
                "name":"Employee Profile",
                "description": "Manage and update employee information efficiently.",
                "actions": [
                    {
                        "action": Action.CREATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_EMPLOYEES.value, "code": "create_all_employees"},
                            {"name": AccessLevel.NONE.value, "code": "create_employee_none"},


                        ],
                        "description": "Create new employee"
                    },
                    {
                        "action": Action.READ.value,  
                        "access_levels": [
                            {"name": AccessLevel.ALL_EMPLOYEES.value, "code": "read_all_employees"},
                            {"name": AccessLevel.TEAM_EMPLOYEES.value, "code": "read_team_employees"},
                            {"name": AccessLevel.OWN_EMPLOYEES.value, "code": "read_own_employees"},

                        ],
                        "description": "View employee information"
                    },
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_EMPLOYEES.value, "code": "update_all_employees"},
                            {"name": AccessLevel.TEAM_EMPLOYEES.value, "code": "update_team_employees"},
                            {"name": AccessLevel.OWN_EMPLOYEES.value, "code": "update_own_employees"},
                            {"name": AccessLevel.NONE.value, "code": "employee_update_none"}
                        ],
                        "description": "Update employee information"
                    },                    
                ],
                "permission_set": EMPLOYEE_PERMISSION_SET

                
            },
            
            "document": {
                "id":3,
                "name":"Document",
                "description": "Store, organize, and access employee documents securely.",
                "actions": [
                    
                     {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_DOCUMENTS.value, "code": "read_all_documents"},
                            {"name": AccessLevel.TEAM_DOCUMENTS.value, "code": "read_team_documents"},
                            {"name": AccessLevel.OWN_DOCUMENTS.value, "code": "read_own_documents"},

                            # {"name": AccessLevel.NONE.value, "code": "read_document_none"}
                        ],
                        "description": "View document"
                    },
                     
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_DOCUMENTS.value, "code": "import_all_documents"},
                            {"name": AccessLevel.TEAM_DOCUMENTS.value, "code": "import_team_documents"},
                            {"name": AccessLevel.OWN_DOCUMENTS.value, "code": "import_own_documents"},
                            {"name": AccessLevel.NONE.value, "code": "import_document_none"}
                        ],
                        "description": "Upload document"
                    },
                   
                    {
                        "action": Action.DELETE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_DOCUMENTS.value, "code": "delete_all_documents"},
                            {"name": AccessLevel.TEAM_DOCUMENTS.value, "code": "delete_team_documents"},
                            {"name": AccessLevel.OWN_DOCUMENTS.value, "code": "delete_own_documents"},
                            {"name": AccessLevel.NONE.value, "code": "delete_document_none"}
                        ],
                        "description": "Delete documents"
                    }
                ],
                "permission_set": DOCUMENT_PERMISSION_SET

            },
            "acknowledgement": {
                "id":4,
                "name":"Acknowledgement",
                "description": "Track employee acknowledgements for key updates.",
                "actions": [
                    {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_ACKNOWLEDGEMENTS.value, "code": "read_all_acknowledgements"},
                            {"name": AccessLevel.TEAM_ACKNOWLEDGEMENTS.value, "code": "read_team_acknowledgements"}
                        ],
                        "description": "Acknowledgement"
                    }
                ]
            }
        }
    },
    "client_management": {
        "features": {
            "client_profile": {
                "id":5,
                "name":"Client Profile",
                "description": "Manage client information effectively.",
                "actions": [
                    {
                        "action": Action.CREATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_CLIENTS.value, "code": "create_all_clients"},
                            {"name": AccessLevel.NONE.value, "code": "create_client_none"},
                        ],
                        "description": "Create new client"
                    },
                       {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_CLIENTS.value, "code": "read_all_clients"},
                            {"name": AccessLevel.TEAM_CLIENTS.value, "code": "read_team_clients"}
                        ],
                        "description": "View client details"
                    },
                    {

                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_CLIENTS.value, "code": "update_all_clients"},
                            {"name": AccessLevel.TEAM_CLIENTS.value, "code": "update_clients_team_owns"},
                            {"name": AccessLevel.NONE.value, "code": "client_update_none"}
                        ],
                        "description": "Update client information"
                    }
                 
                ],
                "permission_set": CLIENT_PERMISSION_SET

            },
            "risk_assessment": {
                "id":6,
                "name":"Risk Assessment",
                "description": "Perform risk assessments for clients.",
                "actions": [
                    {
                        "action": Action.CREATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_RISK_ASSESSMENTS.value, "code": "create_all_risk_assessments"},
                            {"name": AccessLevel.TEAM_RISK_ASSESSMENTS.value, "code": "create_risk_assessments_team_own"},
                            {"name": AccessLevel.OWN_RISK_ASSESSMENTS.value, "code": "create_risk_assessments_of_their_own"},

                            # {"name": AccessLevel.NONE.value, "code": "create_none"}
                        ],
                        "description": "Create new risk assessment"
                    },
                    {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_RISK_ASSESSMENTS.value, "code": "read_all_risk_assessments"},
                            {"name": AccessLevel.TEAM_RISK_ASSESSMENTS.value, "code": "read_risk_assessments_team_own"},
                            {"name": AccessLevel.OWN_RISK_ASSESSMENTS.value, "code": "read_risk_assessments_of_their_own"},

                            # {"name": AccessLevel.NONE.value, "code": "read_none"}
                        ],
                        "description": "View risk assessment"
                    },
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_RISK_ASSESSMENTS.value, "code": "update_all_risk_assessments"},
                            {"name": AccessLevel.TEAM_RISK_ASSESSMENTS.value, "code": "update_team_risk_assessments"},
                            {"name": AccessLevel.NONE.value, "code": "risk_assessment_update_none"},

                            # {"name": AccessLevel.OWN_RISK_ASSESSMENTS.value, "code": "update_own_risk_assessments"},
                        ],
                        "description": "Update existing risk assessment"
                    },
                    
                    # {
                    #     "action": Action.DELETE.value,
                    #     "access_levels": [
                    #         {"name": AccessLevel.ALL_RISK_ASSESSMENTS.value, "code": "delete_all_risk_assessments"},
                    #         {"name": AccessLevel.TEAM_RISK_ASSESSMENTS.value, "code": "delete_risk_assessments_team_own"},
                    #     ],
                    #     "description": "Delete risk assessment"
                    # },
                ],
                "permission_set": RISK_ASSESSMENT_PERMISSION_SET

            },
            # "service_delivery_team": {
            #     "id":7,
            #     "name":"Service Delivery Team",
            #     "description": "Manage team assignments effectively.",
            #     "actions": [
            #         {
            #             "action": Action.UPDATE.value,
            #             "access_levels": [
            #                 {"name": AccessLevel.ALL_SERVICES.value, "code": "update_all_services"},
            #                 {"name": AccessLevel.TEAM_SERVICES.value, "code": "update_service_their_team_own"},
            #                 # {"name": AccessLevel.OWN_SERVICES.value, "code": "update_service_of_their_own"},
            #                 {"name": AccessLevel.NONE.value, "code": "update_none"}
            #             ],
            #             "description": "Create risk assessment"
            #         },
            #         {
            #             "action": Action.READ.value,
            #             "access_levels": [
            #                 {"name": AccessLevel.ALL_SERVICES.value, "code": "read_all_services"},
            #                 {"name": AccessLevel.TEAM_SERVICES.value, "code": "read_service_their_team_own"},
            #             ],
            #             "description": "Update risk assessment"
            #         }
            #     ]
            # }
        }
    },
    "department_management": {
        "features": {
            "department_management": {
                "id":8,
                "name":"Team Management",
                "description": "Manage and maintain client teams.",
                "actions": [
                    {
                        "action": Action.CREATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_DEPARTMENTS.value, "code": "create_department_all"},
                            {"name": AccessLevel.TEAM_DEPARTMENTS.value, "code": "create_department_team_own"},

                        ],
                        "description": "Create client Team"
                    },
                     {
                        "action": Action.READ.value,
                        "access_levels": [

                            {"name": AccessLevel.ALL_DEPARTMENTS.value, "code": "read_department_all"},
                            {"name": AccessLevel.TEAM_DEPARTMENTS.value, "code": "read_department_own"},

                        ],
                        "description": "View Client Team"
                    },
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_DEPARTMENTS.value, "code": "update_department_all"},
                            {"name": AccessLevel.TEAM_DEPARTMENTS.value, "code": "update_department_own"},
                            {"name": AccessLevel.NONE.value, "code": "update_department_none"}

                        ],
                        "description": "Update Client Team"
                    },
                    {
                        "action": Action.DELETE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_DEPARTMENTS.value, "code": "delete_custom_department_all"},
                            {"name": AccessLevel.TEAM_DEPARTMENTS.value, "code": "delete_department_own"},
                            {"name": AccessLevel.NONE.value, "code": "delete_department_none"}

                        ],
                        "description": "Delete Client Team"
                    }
                ],
                "permission_set": DEPARTMENT_PERMISSION_SET

            },
            "assigning_clients": {
                "id":9,
                "name":"Assigning Clients",
                "description": "Assign managers and clients to teams.",
                "actions": [
           
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_CLIENTS.value, "code": "update_clients_to_department"},
                            {"name": AccessLevel.TEAM_CLIENTS.value, "code": "update_own_clients_to_department"}

                        ],
                        "description": "Assign Clients to Team"
                    }
                ]
            }
        }
    },
    
    "roster_management": {
        "features": {
            "shift_dashboard": {
                "id":10,
                "name":"Shift Dashboard",
                "description": "Manage and view client shifts on the dashboard.",
                "actions": [
                    {
                        "action": Action.CREATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_SHIFTS.value, "code": "create_shift_all"},
                            {"name": AccessLevel.TEAM_SHIFTS.value, "code": "create_own_team_shift"},
                            {"name": AccessLevel.NONE.value, "code": "create_shift_none"},

                            
                        ],
                        "description": "Create Client Shift"
                    },
                    {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_SHIFTS.value, "code": "read_client_shift_all"},
                            {"name": AccessLevel.TEAM_SHIFTS.value, "code": "read_own_team_shift"},
                            {"name": AccessLevel.OWN_SHIFTS.value, "code":  "read_own_shift"},
                            # {"name": AccessLevel.NONE.value, "code": "read_no_shift_access"}
                        ],
                        "description": "View Client Shift"
                    },
             
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_SHIFTS.value, "code": "update_shift_all"},
                            {"name": AccessLevel.TEAM_SHIFTS.value, "code": "update_own_team_shift"},
                            {"name": AccessLevel.NONE.value, "code": "update_roster_shift_none"},


                        ],
                        "description": "Update Client Shift"
                    },
                    {
                        "action": Action.DELETE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_SHIFTS.value, "code": "delete_shift_all"},
                            {"name": AccessLevel.TEAM_SHIFTS.value, "code": "delete_own_team_shift"},
                            {"name": AccessLevel.NONE.value, "code": "delete_no_shift_access"}

                            
                        ],
                        "description": "Delete Client Shift"
                    }
                ],
                
                "permission_set": SHIFT_DASHBOARD_PERMISSION_SET

            },
            "shift_report": {
                "id":11,
                "name":"Shift Report",
                "description": "Download client shift reports.",
                "actions": [
                
                    {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_SHIFT_REPORTS.value, "code": "view_all_shift_reports"},
                            {"name": AccessLevel.TEAM_SHIFT_REPORTS.value, "code": "view_own_team_shift_reports"}
                        ],
                        "description": "View Shift Report"
                    },
                        {
                        "action": Action.EXPORT.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_SHIFT_REPORTS.value, "code": "export_all_shift_reports"},
                            {"name": AccessLevel.TEAM_SHIFT_REPORTS.value, "code": "export_own_team_shift_reports"},
                            {"name": AccessLevel.NONE.value, "code": "export_shift_reports_none"}

                        ],
                        "description": "Download Shift Report"
                        
                    }
                ],
                
                "permission_set": SHIFT_REPORT_PERMISSION_SET
            },
            # "roster": {
            #     "id":12,
            #     "name":"Roster",
            #     "description": "Manage rosters and employee punch-in/punch-out actions.",
            #     "actions": [
            #         {
            #             "action": Action.UPDATE.value,
            #             "access_levels": [
            #                 {"name": AccessLevel.ALL_ROSTERS.value, "code": "update_employee_punch_in_out_all_rosters"},
            #                 {"name": AccessLevel.TEAM_ROSTERS.value, "code": "update_employee_punch_in_out_own_team_shifts"},
            #                 {"name": AccessLevel.OWN_ROSTERS.value, "code": "update_employee_punch_in_out_own_shifts"},
            #                 {"name": AccessLevel.NONE.value, "code": "update_employee_punch_in_out_no_access"}#again no read permission here need to update
            #             ],
            #             "description": "Employee will start the shift by Punching In and Punching Out"
            #         }
            #     ]
            # }
        }
    },
    "settings": {
        "features": {
            "terms_and_conditions": {
                "id":13,
                "name":"Terms and Conditions",
                "description": "Define and manage company-wide terms and conditions.",
                "actions": [
                    # {
                    #     "action": Action.CREATE.value,
                    #     "access_levels": [
                    #         {"name": AccessLevel.ALL_TERMS_AND_CONDITONS.value, "code": "create_terms_and_conditions_all"},
                    #         {"name": AccessLevel.NONE.value, "code": "create_none_terms_and_conditions"}
                    #     ],
                    #     "description": "Create new terms and conditions"
                    # },

                    {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_TERMS_AND_CONDITONS.value, "code": "view_terms_and_conditions_all"},
                            {"name": AccessLevel.NONE.value, "code": "view_none_terms_and_conditions"},

                        ],
                        "description": "View terms and conditions"
                    },
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.NONE.value, "code": "update_none_terms_and_conditions"},
                            {"name": AccessLevel.ALL_TERMS_AND_CONDITONS.value, "code": "update_terms_and_conditions_all"},

                        ],
                        "description": "Update terms and conditions"
                    }
                ],
                 "permission_set": TERMS_AND_CONDITIONS_PERMISSION_SET

            },
            "privacy_policy": {
                "id":14,
                "name":"Privacy Policy",
                "description": "Define and manage company-wide privacy policies.",
                "actions": [
                    # {
                    #     "action": Action.CREATE.value,
                    #     "access_levels": [
                    #         {"name": AccessLevel.ALL_PRIVACY_POLICY.value, "code": "create_privacy_policy_all"},
                    #         {"name": AccessLevel.NONE.value, "code": "create_none_privacy_policy"}
                    #     ],
                    #     "description": "Create new privacy policy"
                    # },
             
                    {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_PRIVACY_POLICY.value, "code": "view_privacy_policy_all"},
                            {"name": AccessLevel.NONE.value, "code": "view_none_privacy_policy"}
                        ],
                        "description": "View privacy policy"
                    },
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                             {"name": AccessLevel.NONE.value, "code": "update_none_privacy_policy"},
                            {"name": AccessLevel.ALL_PRIVACY_POLICY.value, "code": "update_privacy_policy_all"},

                        ],
                        "description": "Update privacy policy"
                    }
                ],
                "permission_set": PRIVACY_POLICY_PERMISSION_SET

            },
            # "hierarchy": {
            #     "id":15,
            #     "name":"Hierarchy",
            #     "description": "Setup the Hierarchy for Investigation",
            #     "actions": [
            #         {
            #             "action": Action.CREATE.value,
            #             "access_levels": [
            #                 {"name": AccessLevel.ALL_HIERARCHY.value, "code": "create_hierarchy_all"},
            #                 {"name": AccessLevel.NONE.value, "code": "create_none_hierarchy"}
            #             ],
            #             "description": "Setup New Hierarchy"
            #         },
            #         {
            #             "action": Action.UPDATE.value,
            #             "access_levels": [
            #                 {"name": AccessLevel.ALL_HIERARCHY.value, "code": "update_hierarchy_all"},
            #                 {"name": AccessLevel.NONE.value, "code": "update_none_hierarchy"}
            #             ],
            #             "description": "Update Hierarchy"
            #         },
            #         {
            #             "action": Action.READ.value,
            #             "access_levels": [
            #                 {"name": AccessLevel.ALL_HIERARCHY.value, "code": "read_hierarchy_all"},
            #                 {"name": AccessLevel.NONE.value, "code": "read_none_hierarchy"}
            #             ],
            #             "description": "view Hierarchy"
            #         },
            #     ]
            # },
            "user_permissions": {
                "id":16,
                "name":"User Permissions",
                "description": "Allows the user to define and manage the templates for ACL",
                "actions": [
                    {
                        "action": Action.CREATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_PERMISSION.value, "code": "create_templates"},
                            {"name": AccessLevel.NONE.value, "code": "create_templates_none"},

                        ],
                        "description": "Add new template"
                    },
                
                    {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_PERMISSION.value, "code": "read_templates"},
                            {"name": AccessLevel.NONE.value, "code": "read_templates_none"},

                        ],
                        "description": "View template"
                    },
                        {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.NONE.value, "code": "update_templates_none"},
                            {"name": AccessLevel.ALL_PERMISSION.value, "code": "update_templates"},

                        ],
                        "description": "Edit template "
                    }
                ],
                "permission_set": USER_PERMISSION_SET

            }
        }
    },
    "client_incident_report": {
        "features": {
            "client_incident_report": {
                "id":17,
                "name":"Client Incident Report",
                "description": "Record and manage incidents involving clients.",
                "actions": [
                    {
                        "action": Action.CREATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_CLIENT_INCIDENT_REPORT.value, "code": "create_incident_all"},
                            {"name": AccessLevel.TEAM_CLIENT_INCIDENT_REPORT.value, "code": "create_incident_own_team"},
                            {"name": AccessLevel.OWN_CLIENT_INCIDENT_REPORT.value, "code": "create_incident_there_own"},

                            # {"name": AccessLevel.NONE.value, "code": "create_no_access_to_incidents"}

                        ],
                        "description": "Create New Incident"
                    },
                     {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_CLIENT_INCIDENT_REPORT.value, "code": "view_incident_all"},
                            {"name": AccessLevel.TEAM_CLIENT_INCIDENT_REPORT.value, "code": "view_incident_own_team"},
                            {"name": AccessLevel.OWN_CLIENT_INCIDENT_REPORT.value, "code": "view_incident_own"},
                            {"name": AccessLevel.NONE.value, "code": "view_incident_no_access"}
                        ],
                        "description": "View Incident"
                    },
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_CLIENT_INCIDENT_REPORT.value, "code": "update_incident_all"},
                            {"name": AccessLevel.TEAM_CLIENT_INCIDENT_REPORT.value, "code": "update_incident_own_team"},
                            {"name": AccessLevel.NONE.value, "code": "update_incident_no_access"}

                        ],
                        "description": "Update Incident"
                    },
                   
                    {
                        "action": Action.EXPORT.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_CLIENT_INCIDENT_REPORT.value, "code": "export_incident_report_all"},
                            {"name": AccessLevel.TEAM_CLIENT_INCIDENT_REPORT.value, "code": "export_incident_report_own_team"},
                            {"name": AccessLevel.NONE.value, "code": "export_incident_no_access"}

                        ],
                        "description": "Download Incident Report"
                    }
                ],
                "permission_set": INCIDENT_PERMISSION_SET

            },
            # "incident_report": {
            #     "id":2,
            #     "name":"Incident Report",
            #     "description": "Generate and manage incident reports.",
            #     "actions": [
            #         {
            #             "action": Action.DELETE.value,
            #             "access_levels": [
            #                 {"name": AccessLevel.ALL_CLIENT_INCIDENT_REPORT.value, "code": "delete_incident_report_all"},
            #                 {"name": AccessLevel.TEAM_CLIENT_INCIDENT_REPORT.value, "code": "delete_incident_report_own_team"},
            #             ],
            #             "description": "Delete Incident Report"
            #         },
            #         {
            #             "action": Action.EXPORT.value,
            #             "access_levels": [
            #                 {"name": AccessLevel.ALL_CLIENT_INCIDENT_REPORT.value, "code": "export_incident_report_all"},
            #                 {"name": AccessLevel.TEAM_CLIENT_INCIDENT_REPORT.value, "code": "export_incident_report_own_team"},
            #             ],
            #             "description": "Download Incident Report"
            #         }
            #     ]
            # }
        }
    },
    "progress_notes_and_timesheet": {
        "features": {
            "progress_notes_and_timesheet": {
                "id":18,
                "name":"Progress Notes and Timesheet",
                "description": "Record and review progress notes and timesheets.",
                "actions": [
                    {
                        "action": Action.CREATE.value,
                        "access_levels": [

                            {"name": AccessLevel.OWN_PROGRESS_NOTES.value, "code": "create_progress_notes_own"},
                            {"name": AccessLevel.NONE.value, "code": "create_progress_notes_no_access"}
                        ],
                        "description": "Create Progress Notes"
                    },
                     {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_PROGRESS_NOTES.value, "code": "view_progress_notes_all"},
                            {"name": AccessLevel.TEAM_PROGRESS_NOTES.value, "code": "view_progress_notes_own_team"},
                            {"name": AccessLevel.OWN_PROGRESS_NOTES.value, "code": "view_progress_notes_own"},
                            {"name": AccessLevel.NONE.value, "code": "view_progress_notes_no_access"}
                        ],
                        "description": "View Progress Report"
                    },
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_PROGRESS_NOTES.value, "code": "update_progress_notes_all"},
                            {"name": AccessLevel.TEAM_PROGRESS_NOTES.value, "code": "update_progress_notes_own_team"},
                            {"name": AccessLevel.OWN_PROGRESS_NOTES.value, "code": "update_progress_notes_own"},
                            {"name": AccessLevel.NONE.value, "code": "update_progress_notes_no_access"}
                        ],
                        "description": "Update Progress Notes"
                    },
                   
                    {
                        "action": Action.EXPORT.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_PROGRESS_NOTES.value, "code": "export_progress_notes_all"},
                            {"name": AccessLevel.TEAM_PROGRESS_NOTES.value, "code": "export_progress_notes_own_team"},
                            {"name": AccessLevel.NONE.value, "code": "export_none"}

                        ],
                        "description": "Export Progress Report"
                    }
                ],
                
                "permission_set": PROGRESS_NOTES_AND_TIMESHEET_PERMISSION_SET

            },
        }
    },
    "admin_control": {
        "features": {
            "incident_investigation": {
                "id":19,
                "name":"Incident Investigation",
                "description": "Oversee and document incident investigations.",
                "actions": [
                     {
                        "action": Action.READ.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_INCIDENT_INVESTIGATIONS.value, "code": "read_incident_investigation_all"},
                            {"name": AccessLevel.TEAM_CLIENT_INCIDENT_REPORT.value, "code": "read_incident_investigation_own_team"},
                            {"name": AccessLevel.SELF_INCIDENT_INVESTIGATIONS.value, "code": "read_incident_investigation_self"},
                            {"name": AccessLevel.NONE.value, "code": "read_incident_investigation_none"},


                        ],
                        "description": "View incident investigation"
                    },
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_INCIDENT_INVESTIGATIONS.value, "code": "update_incident_investigation_all"},
                            {"name": AccessLevel.TEAM_CLIENT_INCIDENT_REPORT.value, "code": "update_incident_investigation_own_team"},
                            {"name": AccessLevel.SELF_INCIDENT_INVESTIGATIONS.value, "code": "update_incident_investigation_self"},
                            {"name": AccessLevel.NONE.value, "code": "update_incident_investigation_none"},

                        ],
                        "description": "Update incident investigation"
                    }
                   
                ],
                "permission_set": INCIDENT_INVESTIGATION_PERMISSION_SET

                
            },
            "risk_investigation": {
                "id":20,
                "name":"Risk Investigation",
                "description": "Focused on thorough evaluation and validation for Risk Investigation.",
                "actions": [
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_RISK_INVESTIGATIONS.value, "code": "authorize_risk_assessment_all"},
                            {"name": AccessLevel.TEAM_RISK_INVESTIGATIONS.value, "code": "authorize_risk_assessment_own_team"},
                        ],
                        "description": "Update risk investigation"
                    },
                    # read option not available
                    # {
                    #     "action": Action.UPDATE.value,
                    #     "access_levels": [
                    #         {"name": AccessLevel.ALL_RISK_INVESTIGATIONS.value, "code": "authorize_risk_assessment_all"},
                    #         {"name": AccessLevel.TEAM_RISK_INVESTIGATIONS.value, "code": "authorize_risk_assessment_own_team"},
                    #     ],
                    #     "description": "Risk Assessment Authorized By"
                    # }
                ]
            },
            "employee_approval": {
                "id":21,
                "name":"Employee Approval",
                "description": "Facilitate approval of employee.",
                "actions": [
                    {
                        "action": Action.UPDATE.value,
                        "access_levels": [
                            {"name": AccessLevel.ALL_EMPLOYEES.value, "code": "update_employee_approval_all"},
                            {"name": AccessLevel.NONE.value, "code": "update_employee_approval_none"},

                        ],
                        "description": "Can approve the employee in the system"
                    },
                ]
            }
        }
    },

}


def get_all_features_data():
    return DEFAULT_FEATURE_DICT

