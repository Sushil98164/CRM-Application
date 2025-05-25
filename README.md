# CRM-Application
A Customer Relationship Management application built with Django 5.0 and Python 3.12.

## Prerequisites

- Python 3.12 
- pip (Python package installer)
- Git

## Installation

### 1. Clone the Repository

```bash
git clone [<repository-url>](https://github.com/Sushil98164/CRM-Application.git)
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

## Environment Variables

Create a `.env` file in the root directory and add the following variables:

```env
AWS_SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

## Tech Stack

- **Backend:** Django 5.0
- **Language:** Python 3.12
- **Database:** SQLite (default), PostgreSQL/MySQL (production)
- **Frontend:** HTML, CSS, JavaScript (Django templates)

