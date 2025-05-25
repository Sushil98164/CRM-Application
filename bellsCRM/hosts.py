# your_project_name/hosts.py

from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'www', 'bellsCRM.urls', name='www'),
    host(r'(?!www).*', 'bellsCRM.urls', name='subdomains'),
    # Add more host patterns as needed
)

