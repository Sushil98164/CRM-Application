# CRM-Application
A Customer Relationship Management application built with Django 5.0 and Python 3.12.

## Prerequisites

- Python 3.12 
- pip (Python package installer)
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd CRM-Application
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Alternative for some systems
python3 -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
# Command Prompt
venv\Scripts\activate

# PowerShell
venv\Scripts\Activate.ps1

# Git Bash
source venv/Scripts/activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Requirements

```bash
pip install -r requirements.txt
```

### 5. Database Setup

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Project Structure

```
CRM-Application/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
├── venv/                 # Virtual environment (not tracked in git)
├── crm_project/          # Main project directory
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── apps/                 # Django applications
    └── ...
```

## Environment Variables

Create a `.env` file in the root directory and add the following variables:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install new package
pip install package-name
pip freeze > requirements.txt  # Update requirements

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Collect static files (for production)
python manage.py collectstatic
```

## Development

### Adding New Dependencies

1. Activate virtual environment
2. Install the package: `pip install package-name`
3. Update requirements: `pip freeze > requirements.txt`
4. Commit the updated requirements.txt

### Database Changes

1. Make model changes in your Django apps
2. Create migrations: `python manage.py makemigrations`
3. Review the migration files
4. Apply migrations: `python manage.py migrate`

## Deactivating Virtual Environment

```bash
deactivate
```

## Troubleshooting

### Virtual Environment Issues

- **Windows PowerShell execution policy error:**
  ```bash
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

- **Permission denied on activation:**
  - Make sure you have proper permissions
  - Try running terminal as administrator (Windows)

### Database Issues

- **Migration conflicts:**
  ```bash
  python manage.py migrate --fake-initial
  ```

- **Reset migrations:**
  ```bash
  # Delete migration files (keep __init__.py)
  python manage.py makemigrations
  python manage.py migrate
  ```

### Requirements Installation Issues

- **Upgrade pip:**
  ```bash
  python -m pip install --upgrade pip
  ```

- **Install specific package version:**
  ```bash
  pip install package-name==version
  ```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Test your changes
4. Submit a pull request

## Tech Stack

- **Backend:** Django 5.0
- **Language:** Python 3.12
- **Database:** SQLite (default), PostgreSQL/MySQL (production)
- **Frontend:** HTML, CSS, JavaScript (Django templates)

## License

[Add your license information here]

## Contact

[Add your contact information here]
