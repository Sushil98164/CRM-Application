EMPLOYEE_PERMISSION_SET = {
    "create": {
        "create_all_employees": {
            "update": []
        },
        "create_employee_none": {
            "update": []
        },
    },
    "read": {
        "read_all_employees": {
            "update": [
                { "code": "update_all_employees", "name": "All employees", 'access_level':'all' },
                { "code": "update_team_employees", "name": "Employees their team owns",'access_level':'team' },
                { "code": "update_own_employees", "name": "Self" ,'access_level':'own' },
                { "code": "employee_update_none", "name": "None",'access_level':'none' }
            ]
        },
        "read_team_employees": {
            "update": [
                { "code": "update_team_employees", "name": "Employees their team owns", 'access_level':'team' },
                { "code": "update_own_employees", "name": "Self",'access_level':'own' },
                { "code": "employee_update_none", "name": "None",'access_level':'none' }
            ]
        },
        "read_own_employees": {
            "update": [
                { "code": "update_own_employees", "name": "Self" ,'access_level':'own'},
                { "code": "employee_update_none", "name": "None" , 'access_level':'none' }
            ]
        },
    },
    
    "update": {
        "update_all_employees": {
            "read": [
                { "code": "read_all_employees", "name": "All employees",  'access_level':'all'  }
            ]
        },
        "update_team_employees": {
            "read": [
                { "code": "read_all_employees", "name": "All employees", 'access_level':'all' },
                { "code": "read_team_employees", "name": "Employees their team owns" ,'access_level':'team'}
            ]
        },
        "update_own_employees": {
            "read": [
                { "code": "read_all_employees", "name": "All employees",  'access_level':'all' },
                { "code": "read_team_employees", "name": "Employees their team owns", 'access_level':'team' },
                { "code": "read_own_employees", "name": "Employees of their own", 'access_level':'own' }
            ]
        },
        "employee_update_none": {
            "read": [
                { "code": "read_all_employees", "name": "All employees", 'access_level':'all' },
                { "code": "read_team_employees", "name": "Employees their team owns", 'access_level':'team' },
                { "code": "read_own_employees", "name": "Employees of their own", 'access_level':'own' }
            ]
        },
    }
}



DOCUMENT_PERMISSION_SET = {
    "read": {
        "read_all_documents": {
            "update": [
                { "code": "import_all_documents", "name": "All documents",'access_level':'all' },
                { "code": "import_team_documents", "name": "Documents their team owns",'access_level':'team' },
                { "code": "import_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "import_document_none", "name": "None", 'access_level':'none' }
            ],
            "delete": [
                { "code": "delete_all_documents", "name": "All Documents", 'access_level':'all' },
                { "code": "delete_team_documents", "name": "Documents their team owns", 'access_level':'team'  },
                { "code": "delete_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "delete_document_none", "name": "None", 'access_level':'none' }
            ]
        },
        "read_team_documents": {
            "update": [
                { "code": "import_team_documents", "name": "Documents their team owns" ,'access_level':'team' },
                { "code": "import_own_documents", "name": "Document of their own",  'access_level':'own' },
                { "code": "import_document_none", "name": "None", 'access_level':'none' }
            ],
            "delete": [
                { "code": "delete_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                { "code": "delete_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "delete_document_none", "name": "None" , 'access_level':'none'}
            ]
        },
        "read_own_documents": {
            "update": [
                { "code": "import_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "import_document_none", "name": "None", 'access_level':'none' }
            ],
            "delete": [
                { "code": "delete_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "delete_document_none", "name": "None",  'access_level':'none' }
            ]
        },
    },
    
    "update": {
        "import_all_documents": {
            "read": [
                { "code": "read_all_documents", "name": "All documents", 'access_level':'all' },
            
            ],
            "delete": [
                { "code": "delete_all_documents", "name": "All Documents", 'access_level':'all' },
                { "code": "delete_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                { "code": "delete_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "delete_document_none", "name": "None", 'access_level':'none' }
            ]
        },
        "import_team_documents": {
            "read": [
                { "code": "read_all_documents", "name": "All documents", 'access_level':'all' },
                { "code": "read_team_documents", "name": "Documents their team owns", 'access_level':'team' }
            ],
            "delete": [
                { "code": "delete_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                { "code": "delete_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "delete_document_none", "name": "None", 'access_level':'none' }
            ]
        },
        "import_own_documents": {
            "read": [
                { "code": "read_all_documents", "name": "All documents", 'access_level':'all' },
                { "code": "read_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "read_document_none", "name": "None",  'access_level':'none' }
            ],
            "delete": [
                { "code": "delete_own_documents", "name": "Document of their own", 'access_level':'own'  },
                { "code": "delete_document_none", "name": "None", 'access_level':'none'  }
            ]
        },
        "import_document_none": {
            "read": [
                { "code": "read_all_documents", "name": "All documents", 'access_level':'all' },
                { "code": "read_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                { "code": "read_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "read_document_none", "name": "None", 'access_level':'none' }
            ],
            "delete": [
                { "code": "delete_all_documents", "name": "All Documents", 'access_level':'all' },
                { "code": "delete_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                { "code": "delete_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "delete_document_none", "name": "None", 'access_level':'none' }
            ]
        }
    },

    "delete": {
        "delete_all_documents": {
            "read": [
                { "code": "read_all_documents", "name": "All documents", 'access_level':'all' },
           
            ],
            "update": [
                { "code": "import_all_documents", "name": "All documents", 'access_level':'all' },
                { "code": "import_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                { "code": "import_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "import_document_none", "name": "None", 'access_level':'none' }
            ]
        },
        "delete_team_documents": {
            "read": [
                { "code": "read_all_documents", "name": "All documents", 'access_level':'all' },
                { "code": "read_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                # { "code": "read_own_documents", "name": "Document of their own", 'access_level':'own' },
                # { "code": "read_document_none", "name": "None", 'access_level':'none' }
            ],
            "update": [
                { "code": "import_all_documents", "name": "All documents",  'access_level':'all' },
                { "code": "import_team_documents", "name": "Documents their team owns",  'access_level':'team' },
                { "code": "import_own_documents", "name": "Document of their own",'access_level':'own' },
                { "code": "import_document_none", "name": "None", 'access_level':'none'  }
            ]
        },
        "delete_own_documents": {
            "read": [
                { "code": "read_all_documents", "name": "All documents", 'access_level':'all' },
                { "code": "read_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                { "code": "read_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "read_document_none", "name": "None", 'access_level':'none' }
            ],
            "update": [
                { "code": "import_all_documents", "name": "All documents",  'access_level':'all' },
                { "code": "import_team_documents", "name": "Documents their team owns", 'access_level':'team'  },
                { "code": "import_own_documents", "name": "Document of their own",'access_level':'own' },
                { "code": "import_document_none", "name": "None", 'access_level':'none' }
            ]
        },
        "delete_document_none": {
            "read": [
                { "code": "read_all_documents", "name": "All documents",  'access_level':'all' },
                { "code": "read_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                { "code": "read_own_documents", "name": "Document of their own",'access_level':'own'  },
                { "code": "read_document_none", "name": "None",  'access_level':'none' }
            ],
            "update": [
                { "code": "import_all_documents", "name": "All documents",  'access_level':'all'  },
                { "code": "import_team_documents", "name": "Documents their team owns", 'access_level':'team' },
                { "code": "import_own_documents", "name": "Document of their own", 'access_level':'own' },
                { "code": "import_document_none", "name": "None",  'access_level':'own'}
            ]
        }
    }
}


CLIENT_PERMISSION_SET = {
    
    "create": {
        "create_all_clients": {
            "update": []
        },
        "create_client_none": {
            "update": []
        },
    },
    
    "read": {
        "read_all_clients": {
            "update": [
                { "code": "update_all_clients", "name": "All clients" ,'access_level':'all'},
                { "code": "update_clients_team_owns", "name": "Clients their team owns" ,'access_level':'team'},
                { "code": "client_update_none", "name": "None" ,'access_level':'none'}
            ]
        },
        "read_team_clients": {
            "update": [
                { "code": "update_clients_team_owns", "name": "Clients their team owns" ,'access_level':'team'},
                { "code": "client_update_none", "name": "None" ,'access_level':'none'},

            ]
        },
      
    },
    
    "update": {
        "update_all_clients": {
            "read": [
                { "code": "read_all_clients", "name": "All clients",'access_level':'all' }
            ]
        },
        "update_clients_team_owns": {
            "read": [
                { "code": "read_all_clients", "name": "All clients",'access_level':'all' },
                { "code": "read_team_clients", "name": "Clients their team owns" ,'access_level':'own'}
            ]
        },
        "client_update_none": {
            "read": [
                { "code": "read_all_clients", "name": "All clients" ,'access_level':'all'},
                { "code": "read_team_clients", "name": "Clients their team owns",'access_level':'team' }
            ]
        },
    }
}



RISK_ASSESSMENT_PERMISSION_SET = {
    "create": {
        "create_all_risk_assessments":{
            "read": [
                { "code": "read_all_risk_assessments", "name": "All risk assessments" ,'access_level':'all'},
                { "code": "read_risk_assessments_team_own", "name": "Risk assessments their team owns" ,'access_level':'team'},
                { "code": "read_risk_assessments_of_their_own", "name": "Risk assessments of their own" ,'access_level':'own'},

            ],
            "update": [
                { "code": "update_all_risk_assessments", "name": "All risk assessments" ,'access_level':'all'},
                { "code": "update_team_risk_assessments", "name": "Risk assessments their team owns",'access_level':'team' },
                { "code": "risk_assessment_update_none", "name": "None",'access_level':'none' }

            ],      
        },
        "create_risk_assessments_team_own":{
            "read": [
                { "code": "read_risk_assessments_team_own", "name": "Risk assessments their team owns" ,'access_level':'team'},
                { "code": "read_risk_assessments_of_their_own", "name": "Risk assessments of their own",'access_level':'own' }

            ],
            "update": [
                { "code": "update_team_risk_assessments", "name": "Risk assessments their team owns" ,'access_level':'team'},
                { "code": "risk_assessment_update_none", "name": "None",'access_level':'none' }

            ],        
        },
        "create_risk_assessments_of_their_own":{
            "read": [
                { "code": "read_risk_assessments_of_their_own", "name": "Risk assessments of their own" ,'access_level':'own'}

            ],
            "update": [
                { "code": "risk_assessment_update_none", "name": "None" ,'access_level':'none'}

            ],        
        },
    },
    
    "read": {
        "read_all_risk_assessments":{
            "create": [
                { "code": "create_all_risk_assessments", "name": "All risk assessments" ,'access_level':'all'},
            ],
            "update": [
                { "code": "update_all_risk_assessments", "name": "All risk assessments",'access_level':'all' },
                { "code": "update_team_risk_assessments", "name": "Risk assessments their team owns",'access_level':'team' },
                { "code": "risk_assessment_update_none", "name": "None" ,'access_level':'none'}

            ],       
        },
        "read_risk_assessments_team_own":{
            "create": [
                { "code": "create_all_risk_assessments", "name": "All risk assessments",'access_level':'all' },

                { "code": "create_risk_assessments_team_own", "name": "Risk assessments their team owns" ,'access_level':'team'},
            ],
            "update": [
                { "code": "update_team_risk_assessments", "name": "Risk assessments their team owns" ,'access_level':'team'},
                { "code": "risk_assessment_update_none", "name": "None",'access_level':'none' }
            ],         
        },
        "read_risk_assessments_of_their_own":{
            "create": [
                 { "code": "create_all_risk_assessments", "name": "All risk assessments",'access_level':'all' },
                { "code": "create_risk_assessments_team_own", "name": "Risk assessments their team owns" ,'access_level':'team'},
                { "code": "create_risk_assessments_of_their_own", "name": "Risk assessments of their own" ,'access_level':'own'}
            ],
            "update": [
                { "code": "risk_assessment_update_none", "name": "None",'access_level':'none' }

            ],        
        },
    },
    "update": {
        "update_all_risk_assessments":{
            "create": [
                { "code": "create_all_risk_assessments", "name": "All risk assessments",'access_level':'all' },
            ],
            "read": [
                { "code": "read_all_risk_assessments", "name": "All risk assessments" ,'access_level':'all'},
            ],       
        },
        "update_team_risk_assessments":{
            "create": [
                { "code": "create_all_risk_assessments", "name": "All risk assessments",'access_level':'all' },
                { "code": "create_risk_assessments_team_own", "name": "Risk assessments their team owns",'access_level':'team' },

            ],
            "read": [
                { "code": "read_all_risk_assessments", "name": "All risk assessments" ,'access_level':'all'},
                { "code": "read_risk_assessments_team_own", "name": "Risk assessments their team owns",'access_level':'team' },
            ],         
        },
        "risk_assessment_update_none":{
            "create": [
                { "code": "create_all_risk_assessments", "name": "All risk assessments",'access_level':'all' },
                { "code": "create_risk_assessments_team_own", "name": "Risk assessments their team owns",'access_level':'team' },
                { "code": "create_risk_assessments_of_their_own", "name": "Risk assessments of their own" ,'access_level':'own'}
            ],
            "read": [
                { "code": "read_all_risk_assessments", "name": "All risk assessments",'access_level':'all'},
                { "code": "read_risk_assessments_team_own", "name": "Risk assessments their team owns" ,'access_level':'team'},
                { "code": "read_risk_assessments_of_their_own", "name": "Risk assessments of their own" ,'access_level':'own'}
            ],        
        },
    },
    
}


INCIDENT_PERMISSION_SET = {
    "create": {
        "create_incident_all": {
            "read": [
                { "code": "view_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "view_incident_own_team", "name": "Incidents their team owns",'access_level':'team' },
                { "code": "view_incident_own", "name": "Incidents they own" ,'access_level':'own'},
                { "code": "view_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "update": [
                { "code": "update_incident_all", "name": "All Incidents" ,'access_level':'all'},
                { "code": "update_incident_own_team", "name": "Incidents their team owns",'access_level':'team' },
                { "code": "update_incident_no_access", "name": "None",'access_level':'none' }
            ],
            "export": [
                { "code": "export_incident_report_all", "name": "All Incidents" ,'access_level':'all'},
                { "code": "export_incident_report_own_team", "name": "Incidents their team owns",'access_level':'team' },
                { "code": "export_incident_no_access", "name": "None" ,'access_level':'none'}
            ]
        },
        "create_incident_own_team": {
            "read": [
                { "code": "view_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "view_incident_own", "name": "Incidents they own",'access_level':'own' },
                { "code": "view_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "update": [
                { "code": "update_incident_own_team", "name": "Incidents their team owns",'access_level':'team' },
                { "code": "update_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "export": [
                { "code": "export_incident_report_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "export_incident_no_access", "name": "None",'access_level':'none' }
            ]
        },
        "create_incident_there_own": {
            "read": [
                { "code": "view_incident_own", "name": "Incidents they own" ,'access_level':'own'}
            ],
            "update": [
                { "code": "update_incident_no_access", "name": "None",'access_level':'none' }
            ],
            "export": [
                { "code": "export_incident_no_access", "name": "None" ,'access_level':'none'}
            ]
        },
        # "create_no_access_to_incidents": {
        #     "read": [
        #         { "code": "view_incident_all", "name": "All Incidents" },
        #         { "code": "view_incident_own_team", "name": "Incidents their team owns" },
        #         { "code": "view_incident_own", "name": "Incidents they own" },
        #         { "code": "view_incident_no_access", "name": "None" }
        #     ],
        #     "update": [
        #         { "code": "view_incident_all", "name": "All Incidents" },
        #         { "code": "update_incident_all", "name": "All Incidents" },
        #         { "code": "update_incident_own_team", "name": "Incidents their team owns" },
        #         { "code": "update_incident_no_access", "name": "None" }
        #     ],
        #     "export": [
        #         { "code": "export_incident_report_all", "name": "All Incidents" },
        #         { "code": "export_incident_report_own_team", "name": "Incidents their team owns" },
        #         { "code": "export_incident_no_access", "name": "None" }
        #     ]
        # },
    },

    "read": {
        "view_incident_all": {
            "update": [
                { "code": "update_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "update_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "update_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "export": [
                { "code": "export_incident_report_all", "name": "All Incidents" ,'access_level':'all'},
                { "code": "export_incident_report_own_team", "name": "Incidents their team owns",'access_level':'team' },
                { "code": "export_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "create": [
                { "code": "create_incident_all", "name": "All Incidents" ,'access_level':'all'}
               
            ]
        },
        "view_incident_own_team": {
            "update": [
                { "code": "update_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "update_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "export": [
                { "code": "export_incident_report_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "export_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
             "create": [
                { "code": "create_incident_all", "name": "All Incidents" ,'access_level':'all'},
                { "code": "create_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'}
            ]
            
        },
        "view_incident_own": {
            "update": [
                { "code": "update_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "export": [
                { "code": "export_incident_no_access", "name": "None" ,'access_level':'none'}
            ]
        },
        "view_incident_no_access": {
            "update": [
                { "code": "update_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "export": [
                { "code": "export_incident_no_access", "name": "None" ,'access_level':'none'}
            ]
        }
    },

    "update": {
        "update_incident_all": {
            "read": [
                { "code": "view_incident_all", "name": "All Incidents" ,'access_level':'all'},
              
            ],
            "export": [
                { "code": "export_incident_report_all", "name": "All Incidents" ,'access_level':'all'},
                { "code": "export_incident_report_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "export_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "create": [
                { "code": "create_incident_all", "name": "All Incidents" ,'access_level':'all'},
                # { "code": "create_incident_own_team", "name": "Incidents their team owns" },
                # { "code": "create_incident_there_own", "name": "Incidents they own" },


                
            ]
        },
        "update_incident_own_team": {
            "read": [
                { "code": "view_incident_all", "name": "All Incidents" ,'access_level':'all'},
                { "code": "view_incident_own_team", "name": "Incidents their team owns",'access_level':'team' },
                # { "code": "view_incident_own", "name": "Incidents they own" ,'access_level':'own'},
                # { "code": "view_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "create": [
                { "code": "create_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "create_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "create_incident_there_own", "name": "Incidents they own" ,'access_level':'own'},
                
            ],
            "export": [
                { "code": "export_incident_report_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "export_incident_no_access", "name": "None" ,'access_level':'none'}
            ]
        },
        "update_incident_no_access": {
            "read": [
                { "code": "view_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "view_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "view_incident_own", "name": "Incidents they own" ,'access_level':'own'},
                { "code": "view_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "export": [
                { "code": "export_incident_report_all", "name": "All Incidents" ,'access_level':'all'},
                { "code": "export_incident_report_own_team", "name": "Incidents their team owns",'access_level':'team' },
                { "code": "export_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
             "create": [
                { "code": "create_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "create_incident_own_team", "name": "Incidents their team owns",'access_level':'team' },
                { "code": "create_incident_there_own", "name": "Incidents they own",'access_level':'own' },
                
            ],
        },
    },

    "export": {
        "export_incident_report_all": {
            "read": [
                { "code": "view_incident_all", "name": "All Incidents" ,'access_level':'all'},
                # { "code": "view_incident_own_team", "name": "Incidents their team owns" },
                # { "code": "view_incident_own", "name": "Incidents they own" },
                # { "code": "view_incident_no_access", "name": "None" }
            ],
            "update": [
                { "code": "update_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "update_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "update_incident_no_access", "name": "None" }
            ],
            "create": [
                { "code": "create_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "create_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "create_incident_there_own", "name": "Incidents they own" ,'access_level':'own'},
                
            ],
        },
        "export_incident_report_own_team": {
            "read": [
                { "code": "view_incident_all", "name": "All Incidents" ,'access_level':'all'},
                { "code": "view_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                # { "code": "view_incident_own", "name": "Incidents they own" },
                # { "code": "view_incident_no_access", "name": "None" }
            ],
            "update": [
                { "code": "update_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "update_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "update_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
        },
        "export_incident_no_access": {
            "read": [
                { "code": "view_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "view_incident_own_team", "name": "Incidents their team owns",'access_level':'team' },
                { "code": "view_incident_own", "name": "Incidents they own" ,'access_level':'own'},
                { "code": "view_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "update": [
                { "code": "update_incident_all", "name": "All Incidents",'access_level':'all' },
                { "code": "update_incident_own_team", "name": "Incidents their team owns",'access_level':'team' },
                { "code": "update_incident_no_access", "name": "None" ,'access_level':'none'}
            ],
            "create": [
                { "code": "create_incident_all", "name": "All Incidents" ,'access_level':'all'},
                { "code": "create_incident_own_team", "name": "Incidents their team owns" ,'access_level':'team'},
                { "code": "create_incident_there_own", "name": "Incidents they own" ,'access_level':'own'},
                
            ],
        },
    }
}



DEPARTMENT_PERMISSION_SET = {
     "create": {
        "create_department_all": {
            "update": []
        },
        "create_department_team_own": {
            "update": []
        },
    },
    "read": {
        "read_department_all":{
            "update": [
                { "code": "update_department_all", "name": "All teams" ,'access_level':'all'},
                { "code": "update_department_own", "name": "Teams they own" ,'access_level':'own'},
                { "code": "update_department_none", "name": "None" ,'access_level':'none'}

            ],
            "delete": [
                { "code": "delete_custom_department_all", "name": "All teams",'access_level':'all' },
                { "code": "delete_department_own", "name": "Teams they own" ,'access_level':'own'},
                { "code": "delete_department_none", "name": "None" ,'access_level':'none'}

            ]       
        },
        "read_department_own":{
            "update": [
                { "code": "update_department_own", "name": "Teams they own",'access_level':'own' },
                { "code": "update_department_none", "name": "None" ,'access_level':'none'}

            ],
            "delete": [
                { "code": "delete_department_own", "name": "Teams they own",'access_level':'own' },
                { "code": "delete_department_none", "name": "None" ,'access_level':'none'}

            ]        
        },
    },
    
    "update": {
        "update_department_all":{
            "read": [
                { "code": "read_department_all", "name": "All teams" ,'access_level':'all'}
            ],
            "delete": [
                { "code": "delete_custom_department_all", "name": "All teams",'access_level':'all' },
                {"code": "delete_department_own", "name": "Teams they own",'access_level':'own' },
                { "code": "delete_department_none", "name": "None" ,'access_level':'none'},

            ]        
        },
        "update_department_own":{
            "read": [
                { "code": "read_department_all", "name": "All teams" ,'access_level':'all'},
                { "code": "read_department_own", "name": "Teams they own" ,'access_level':'own'},
            ],
            "delete": [
                {"code": "delete_department_own", "name": "Teams they own",'access_level':'own' },
                { "code": "delete_department_none", "name": "None" ,'access_level':'none'},

            ]
                   
        },
        "update_department_none":{
            "read": [
                { "code": "read_department_all", "name": "All teams" ,'access_level':'all'},
                { "code": "read_department_own", "name": "Teams they own",'access_level':'own' },
            ],
            "delete": [
                {"code": "delete_custom_department_all", "name": "All teams" ,'access_level':'all'},
                {"code": "delete_department_own", "name": "Teams they own",'access_level':'own' },
                { "code": "delete_department_none", "name": "None" ,'access_level':'none'},

            ]
                   
        },
    },
    
    "delete": {
        "delete_custom_department_all":{
            "read": [
                { "code": "read_department_all", "name": "All teams",'access_level':'all' }
            ],
            "update": [
                { "code": "update_department_all", "name": "All teams" ,'access_level':'all'},
            ]        
        },
        "delete_department_own":{
            "read": [
                { "code": "read_department_all", "name": "All teams" ,'access_level':'all'},
                { "code": "read_department_own", "name": "Teams they own",'access_level':'own' },
            ],
            "update": [
                { "code": "update_department_all", "name": "All teams" ,'access_level':'all'},
                {"code": "update_department_own", "name": "Teams they own" ,'access_level':'own'}
            ],
             
        },
        "delete_department_none":{
            "read": [
                { "code": "read_department_all", "name": "All teams",'access_level':'all' },
                { "code": "read_department_own", "name": "Teams they own",'access_level':'own' },
            ],
            "update": [
                { "code": "update_department_all", "name": "All teams",'access_level':'all' },
                {"code": "update_department_own", "name": "Teams they own",'access_level':'own' }
            ],
             
        },
    }
    
}


SHIFT_DASHBOARD_PERMISSION_SET = {
    "create": {
        "create_shift_all":{
            "read": [
                { "code": "read_client_shift_all", "name": "All shifts",'access_level':'all' },
                { "code": "read_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "read_own_shift", "name": "Shifts of their own" ,'access_level':'own'},
                # { "code": "read_no_shift_access", "name": "None",'access_level':'none' }

            ],
            "update": [
                { "code": "update_shift_all", "name": "All shifts",'access_level':'all' },
                { "code": "update_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none'}

            ],
            "delete": [
                { "code": "delete_shift_all", "name": "All shifts" ,'access_level':'all'},
                { "code": "delete_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "delete_no_shift_access", "name": "None",'access_level':'none' }
            ]        
        },
        "create_own_team_shift":{
            "read": [
                { "code": "read_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "read_own_shift", "name": "Shifts of their own",'access_level':'own' },
                # { "code": "read_no_shift_access", "name": "None",'access_level':'none' }

            ],
            "update": [
                { "code": "update_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none'},


            ],
            "delete": [
                { "code": "delete_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "delete_no_shift_access", "name": "None" ,'access_level':'none'}
            ]         
        },
        "create_shift_none":{
            "read": [
                { "code": "read_client_shift_all", "name": "All shifts" ,'access_level':'all'},
                { "code": "read_own_team_shift", "name": "Shifts their team owns",'access_level':'team' },
                { "code": "read_own_shift", "name": "shifts of their own" ,'access_level':'own'},
                # { "code": "read_no_shift_access", "name": "None" ,'access_level':'none'}


            ],
            "update": [
                { "code": "update_own_team_shift", "name": "Shifts their team owns",'access_level':'team' },
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none'},
                # { "code": "delete_no_shift_access", "name": "None" }


            ],
            "delete": [
                { "code": "delete_shift_all", "name": "All shifts",'access_level':'all' },
                { "code": "delete_own_team_shift", "name": "Shifts their team owns",'access_level':'team' },
                { "code": "delete_no_shift_access", "name": "None" ,'access_level':'none'}
            ]         
        },
    },
    
    "read": {
        "read_client_shift_all":{
            "create": [
                { "code": "create_shift_all", "name": "All shifts",'access_level':'all' },
                #{ "code": "create_own_team_shift", "name": "Shifts their team owns" },
                { "code": "create_shift_none", "name": "None" }

            ],
            "update": [
                { "code": "update_shift_all", "name": "All shifts",'access_level':'all' },
                { "code": "update_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none'}

            ],
            "delete": [
                { "code": "delete_shift_all", "name": "All shifts",'access_level':'all' },
                { "code": "delete_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "delete_no_shift_access", "name": "None" ,'access_level':'none'}
            ]        
        },
        "read_own_team_shift":{
            "create": [
                { "code": "create_shift_all", "name": "All shifts",'access_level':'all' },
                { "code": "create_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "create_shift_none", "name": "None",'access_level':'none' }

            ],
            "update": [
                { "code": "update_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none'}

            ],
            "delete": [
                { "code": "delete_own_team_shift", "name": "Shifts their team owns",'access_level':'team' },
                { "code": "delete_no_shift_access", "name": "None",'access_level':'none' }
            ]         
        },
        "read_own_shift":{
            "create": [
                { "code": "create_shift_all", "name": "All shifts",'access_level':'all' },
                { "code": "create_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team'},
                { "code": "create_shift_none", "name": "None" ,'access_level':'none' }
            ],
            "update": [
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none' }

            ],
            "delete": [
                { "code": "delete_no_shift_access", "name": "None" ,'access_level':'none' }
            ]         
        },
        # "read_no_shift_access":{
        #     "create": [
        #         { "code": "create_shift_none", "name": "None",'access_level':'none'  }
        #     ],
        #     "update": [
        #         { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none' }

        #     ],
        #     "delete": [
        #         { "code": "delete_no_shift_access", "name": "None" ,'access_level':'none' }
        #     ]         
        # },
    },
    "update": {
        "update_shift_all":{
            "create": [
                { "code": "create_shift_all", "name": "All shifts",'access_level':'all'  },
            ],
            "read": [
                { "code": "read_client_shift_all", "name": "All shifts",'access_level':'all'  },
            ],
            "delete": [
                { "code": "delete_shift_all", "name": "All shifts" ,'access_level':'all' },
                { "code": "delete_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team' },
                { "code": "delete_no_shift_access", "name": "None" ,'access_level':'none' }
            ]        
        },
        "update_own_team_shift":{
            "create": [
                { "code": "create_shift_all", "name": "All shifts" ,'access_level':'all' },
                { "code": "create_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team' },

            ],
            "read": [
                { "code": "read_client_shift_all", "name": "All shifts" ,'access_level':'all' },
                { "code": "read_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team' },
            ],
            "delete": [
                { "code": "delete_shift_all", "name": "All shifts" ,'access_level':'all' },
                { "code": "delete_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team' },
                { "code": "delete_no_shift_access", "name": "None" ,'access_level':'none' }
            ]         
        },
        "update_roster_shift_none":{
            "create": [
                { "code": "create_shift_all", "name": "All shifts",'access_level':'all'  },
                { "code": "create_own_team_shift", "name": "Shifts their team owns",'access_level':'team'  },
                { "code": "create_shift_none", "name": "None",'access_level':'none'  }
            ],
            "read": [
                { "code": "read_client_shift_all", "name": "All shifts",'access_level':'all'  },
                { "code": "read_own_team_shift", "name": "Shifts their team owns",'access_level':'team'  },
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none' }

            ],
            "delete": [
                {"code": "delete_shift_all", "name": "All shifts",'access_level':'all'  },
                { "code": "delete_own_team_shift", "name": "Shifts their team owns",'access_level':'team'  },
                { "code": "delete_no_shift_access", "name": "None",'access_level':'none'  }
            ]         
        },
    },
    "delete": {
        "delete_shift_all":{
            "create": [
                { "code": "create_shift_all", "name": "All shifts",'access_level':'all'  },
            ],
            "read": [
                { "code": "read_client_shift_all", "name": "All shifts" ,'access_level':'all' },
            ],
            "update": [
                { "code": "update_shift_all", "name": "All shifts" ,'access_level':'all' },
                { "code": "update_own_team_shift", "name": "Shifts their team owns",'access_level':'team'  },
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none' }

            ]        
        },
        "delete_own_team_shift":{
            "create": [
                { "code": "create_shift_all", "name": "All shifts" ,'access_level':'all' },
                { "code": "create_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team' },

            ],
            "read": [
                { "code": "read_client_shift_all", "name": "All shifts",'access_level':'all'  },
                { "code": "read_own_team_shift", "name": "Shifts their team owns",'access_level':'team'  },
            ],
            "update": [
                { "code": "update_shift_all", "name": "All shifts",'access_level':'all'  },
                { "code": "update_own_team_shift", "name": "Shifts their team owns",'access_level':'team'  },
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none' }                
            ]         
        },
        "delete_no_shift_access":{
            "create": [
                { "code": "create_shift_all", "name": "All shifts" ,'access_level':'all' },
                { "code": "create_own_team_shift", "name": "Shifts their team owns",'access_level':'team'  },
                { "code": "create_shift_none", "name": "None" ,'access_level':'none' }
            ],
            "read": [
                { "code": "read_client_shift_all", "name": "All shifts",'access_level':'all'  },
                { "code": "read_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team' },
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none' }

            ],
            "update": [
                { "code": "update_shift_all", "name": "All shifts" ,'access_level':'all' },
                { "code": "update_own_team_shift", "name": "Shifts their team owns" ,'access_level':'team' },
                { "code": "update_roster_shift_none", "name": "None" ,'access_level':'none' }
            ]              
        },
    },
}


SHIFT_REPORT_PERMISSION_SET = {
    "read": {
        "view_all_shift_reports":{
            "export": [
                { "code": "export_all_shift_reports", "name": "All shift reports" ,'access_level':'all' },
                { "code": "export_own_team_shift_reports", "name": "Shifts report their team owns" ,'access_level':'team' },
                { "code": "export_shift_reports_none", "name": "None" ,'access_level':'none' },

                
            ]         
        },
        "view_own_team_shift_reports":{
            "export": [
                 { "code": "export_own_team_shift_reports", "name": "Shifts report their team owns" ,'access_level':'team' },
                { "code": "export_shift_reports_none", "name": "None" ,'access_level':'none' },
            ]         
        },
    },
    "export": {
        "export_all_shift_reports":{
            "read": [
                { "code": "view_all_shift_reports", "name": "All shift reports" ,'access_level':'all' },
            ]         
        },
        "export_own_team_shift_reports":{
            "read": [
                { "code": "view_all_shift_reports", "name": "All shift reports" ,'access_level':'all' },
                { "code": "view_own_team_shift_reports", "name": "shifts reports their team owns" ,'access_level':'team' },
            ]         
        },
           "export_shift_reports_none":{
            "read": [
                { "code": "view_all_shift_reports", "name": "All shift reports" ,'access_level':'all' },
                { "code": "view_own_team_shift_reports", "name": "shifts reports their team owns" ,'access_level':'team' },

            ]         
        },
    },
    
}





PROGRESS_NOTES_AND_TIMESHEET_PERMISSION_SET = {

    "create": {
        "create_progress_notes_own": {
            "update": []
        },
        "create_progress_notes_no_access": {
            "update": []
        },
    },
    "read": {
        "view_progress_notes_all":{
            "update": [
                { "code": "update_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },
                { "code": "update_progress_notes_own_team", "name": "Progress notes their team owns" ,'access_level':'team' },
                { "code": "update_progress_notes_own", "name": "Progress notes of their own",'access_level':'own' },
                { "code": "update_progress_notes_no_access", "name": "None" ,'access_level':'none' }

            ],
            "export": [
                { "code": "export_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },
                { "code": "export_progress_notes_own_team", "name": "Progress notes their team owns" ,'access_level':'team' },
                { "code": "export_none", "name": "None" ,'access_level':'none' }
            ]        
        },
        "view_progress_notes_own_team":{
            "update": [
                { "code": "update_progress_notes_own_team", "name": "Progress notes their team owns" ,'access_level':'team' },
                { "code": "update_progress_notes_own", "name": "Progress notes of their own",'access_level':'own' },
                { "code": "update_progress_notes_no_access", "name": "None",'access_level':'none'  }

            ],
            "export": [
                { "code": "export_progress_notes_own_team", "name": "Progress notes their team owns" ,'access_level':'team' },
                { "code": "export_none", "name": "None",'access_level':'none'  }
            ]         
        },
        "view_progress_notes_own":{
            "update": [
                { "code": "update_progress_notes_own", "name": "Progress notes of their own" ,'access_level':'own' },
                { "code": "update_progress_notes_no_access", "name": "None",'access_level':'none'  }
            ],
            "export": [
                { "code": "export_none", "name": "None",'access_level':'none'  }
            ]        
        },
        "view_progress_notes_no_access":{
            "update": [
                { "code": "update_progress_notes_no_access", "name": "None" ,'access_level':'none' }

            ],
            "export": [
                { "code": "export_none", "name": "None" ,'access_level':'none' }
            ]        
        },
    },
    "update": {
        "update_progress_notes_all":{
            "read": [
                { "code": "view_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },
                # { "code": "view_progress_notes_own_team", "name": "Progress notes their team owns",'access_level':'team'  },

            ],
             "export": [
                { "code": "export_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },
                { "code": "export_progress_notes_own_team", "name": "Progress notes their team owns" ,'access_level':'team' },
                { "code": "export_none", "name": "None" ,'access_level':'none' }
            ]             
        },
        "update_progress_notes_own_team":{
            "read": [
                { "code": "view_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },
                { "code": "view_progress_notes_own_team", "name": "Progress notes their team owns" ,'access_level':'team' },
            ],
             "export": [
                { "code": "export_progress_notes_own_team", "name": "Progress notes their team owns" ,'access_level':'team' },
                { "code": "export_none", "name": "None",'access_level':'none'  }
            ]            
        },
        "update_progress_notes_own":{
            "read": [
                { "code": "view_progress_notes_all", "name": "All progress notes",'access_level':'all' },
                { "code": "view_progress_notes_own_team", "name": "Progress notes their team owns",'access_level':'team' },
                { "code": "view_progress_notes_own", "name": "Progress notes of their own" ,'access_level':'own' },
            ],
              "export": [
                { "code": "export_none", "name": "None",'access_level':'none'  }
            ]          
        },
        "update_progress_notes_no_access":{
            "read": [
                { "code": "view_progress_notes_all", "name": "All progress notes",'access_level':'all'  },
                { "code": "view_progress_notes_own_team", "name": "Progress notes their team owns",'access_level':'team'  },
                { "code": "view_progress_notes_own", "name": "Progress notes of their own" ,'access_level':'own' },
                { "code": "view_progress_notes_no_access", "name": "None",'access_level':'none'  },
            ],        
        },
    },
    "export": {
        "export_progress_notes_all":{
            "read": [
                { "code": "view_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },
            ],
            "update": [
                { "code": "update_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },


            ]      
        },
        "export_progress_notes_own_team":{
            "read": [
                { "code": "view_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },

                { "code": "view_progress_notes_own_team", "name": "Progress notes their team owns",'access_level':'team'  },
            ], 
            "update": [
                    { "code": "update_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },

                { "code": "update_progress_notes_own_team", "name": "Progress notes their team owns" ,'access_level':'team' },
     

            ]   
        },
        "export_none":{
            "read": [
                { "code": "view_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },
                { "code": "view_progress_notes_own_team", "name": "Progress notes their team owns",'access_level':'team'  },
                { "code": "view_progress_notes_own", "name": "Progress notes of their own",'access_level':'own'  },
                { "code": "view_progress_notes_no_access", "name": "None" ,'access_level':'none' }
            ],  
               "update": [
                { "code": "update_progress_notes_all", "name": "All progress notes" ,'access_level':'all' },
                { "code": "update_progress_notes_own_team", "name": "Progress notes their team owns" ,'access_level':'team' },
                { "code": "update_progress_notes_own", "name": "Progress notes of their own",'access_level':'own' },
                { "code": "update_progress_notes_no_access", "name": "None" ,'access_level':'none' }

            ]       
        },
    },
}



INCIDENT_INVESTIGATION_PERMISSION_SET = {
    
     "read": {
        "read_incident_investigation_all":{
            "update": [
                { "code": "update_incident_investigation_all", "name": "All investigations" ,'access_level':'all' },
                { "code": "update_incident_investigation_own_team", "name": "Incidents their team owns" ,'access_level':'team' },
                { "code": "update_incident_investigation_self", "name": "Incident they own" ,'access_level':'own' },
                { "code": "update_incident_investigation_none", "name": "None",'access_level':'none'  },

            ],        
        },
        "read_incident_investigation_own_team":{
            "update": [
                { "code": "update_incident_investigation_own_team", "name": "Incidents their team owns" ,'access_level':'team' },
                { "code": "update_incident_investigation_self", "name": "Incident they own" ,'access_level':'own' },
                { "code": "update_incident_investigation_none", "name": "None",'access_level':'none'  },

            ],        
        },
        
        "read_incident_investigation_self":{
            "update": [
                { "code": "update_incident_investigation_self", "name": "Incident they own" ,'access_level':'own' },
                { "code": "update_incident_investigation_none", "name": "None",'access_level':'none'  },

            ],        
        },
        
        "read_incident_investigation_none":{
            "update": [
                { "code": "update_incident_investigation_none", "name": "None",'access_level':'none'  },

            ],        
        },
    },
     
    "update": {
        "update_incident_investigation_all":{
            "read": [
                { "code": "read_incident_investigation_all", "name": "All investigations",'access_level':'all'  },

            ],        
        },
        "update_incident_investigation_own_team":{
            "read": [
                { "code": "read_incident_investigation_all", "name": "All investigations" ,'access_level':'all' },
                { "code": "read_incident_investigation_own_team", "name": "Incidents their team owns" ,'access_level':'team' },
                # { "code": "read_incident_investigation_none", "name": "None" },

            ],        
        },
          "update_incident_investigation_none":{
           "read": [
                { "code": "read_incident_investigation_all", "name": "All investigations" ,'access_level':'all' },
                { "code": "read_incident_investigation_own_team", "name": "Incidents their team owns" ,'access_level':'team' },
                { "code": "read_incident_investigation_none", "name": "None" ,'access_level':'none' },

            ],          
        },
    },
   
}





PRIVACY_POLICY_PERMISSION_SET = {
    "read": {
        "view_privacy_policy_all": {
            "update": [],
            "delete": [],
            "export": [],


        },
        "view_none_privacy_policy": {
            "update": [],
            "delete": [],
            "export": [],
        },
    },
     "update": {
        "update_privacy_policy_all": {
            "read": [],
            "delete": [],
            "export": [],
        },
        "update_none_privacy_policy": {
            "read": [],
            "delete": [],
            "export": [],
        },
    },
}
  
  


TERMS_AND_CONDITIONS_PERMISSION_SET = {
    
     "read": {
        "view_terms_and_conditions_all": {
            "update": [],
            "delete": [],
            "export": [],


        },
        "view_none_terms_and_conditions": {
            "update": [],
            "delete": [],
            "export": [],
        },
    },
     "update": {
        "update_none_terms_and_conditions": {
            "read": [],
            "delete": [],
            "export": [],
        },
        "update_none_privacy_policy": {
            "read": [],
            "delete": [],
            "export": [],
        },
    },
     
}



USER_PERMISSION_SET = {
    "create": {
        "create_templates": {
            "update": [],
            "delete": [],
            "export": [],
            "read":[]

        },
        "create_templates_none": {
            "update": [],
            "delete": [],
            "export": [],
            "read":[]

        },
    },
     "read": {
        "read_templates": {
            "update": [],
            "delete": [],
            "export": [],
            "create": []



        },
        "read_templates_none": {
            "update": [],
            "delete": [],
            "export": [],
            "create": []

        },
    },
     "update": {  
        "update_templates_none": {
            "create": [],
            "delete": [],
            "export": [],
            "read": []
        },
        "update_templates": {
            "create": [],
            "delete": [],
            "export": [],
            "read": []
        }
    }
 
}