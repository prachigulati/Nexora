#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Starting build process..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check Django installation
echo "Checking Django installation..."
python -c "import django; print(f'Django version: {django.get_version()}')"

# Check database connection
echo "Checking database connection..."
python manage.py check --database default

# Apply database migrations with force fix
echo "Applying database migrations..."
python manage.py migrate --verbosity=2 || echo "Standard migration failed, trying force fix..."

# Force fix database if needed
echo "Running database force fix..."
python manage.py force_migrate || echo "Force migrate failed, continuing..."

# Emergency database fix if still failing
echo "Running emergency database fix..."
python manage.py shell -c "
from django.db import connection
try:
    from main.models import Project
    project_count = Project.objects.count()
    print(f'Database working: {project_count} projects found')
except Exception as e:
    print(f'Database not working: {e}')
    print('Creating essential tables manually...')
    with connection.cursor() as cursor:
        # Create auth_user table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                password VARCHAR(128) NOT NULL,
                last_login DATETIME,
                is_superuser BOOLEAN NOT NULL,
                username VARCHAR(150) NOT NULL UNIQUE,
                first_name VARCHAR(150) NOT NULL,
                last_name VARCHAR(150) NOT NULL,
                email VARCHAR(254) NOT NULL,
                is_staff BOOLEAN NOT NULL,
                is_active BOOLEAN NOT NULL,
                date_joined DATETIME NOT NULL
            );
        ''')
        
        # Create main_project table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS main_project (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(40) NOT NULL,
                description TEXT NOT NULL,
                problem TEXT,
                market TEXT,
                competition TEXT,
                details TEXT,
                stage VARCHAR(100) NOT NULL,
                category VARCHAR(100) NOT NULL,
                url VARCHAR(200),
                banner VARCHAR(100),
                funding_goal DECIMAL(10,2) NOT NULL,
                created_at DATETIME NOT NULL,
                user_id INTEGER NOT NULL REFERENCES auth_user(id)
            );
        ''')
        
        # Create main_aianalystreport table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS main_aianalystreport (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_score REAL NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                tam_inflation_risk REAL NOT NULL,
                financial_consistency_risk REAL NOT NULL,
                market_saturation_risk REAL NOT NULL,
                competition_risk REAL NOT NULL,
                team_risk REAL NOT NULL,
                growth_score REAL NOT NULL,
                growth_index VARCHAR(20) NOT NULL,
                traction_score REAL NOT NULL,
                hiring_momentum REAL NOT NULL,
                market_demand_score REAL NOT NULL,
                scalability_potential REAL NOT NULL,
                sector_rank INTEGER NOT NULL,
                sector_percentile REAL NOT NULL,
                platform_rank INTEGER NOT NULL,
                platform_percentile REAL NOT NULL,
                vs_sector_avg REAL NOT NULL,
                vs_platform_avg REAL NOT NULL,
                vs_similar_stage REAL NOT NULL,
                risk_analysis TEXT NOT NULL,
                growth_analysis TEXT NOT NULL,
                peer_analysis TEXT NOT NULL,
                recommendations TEXT NOT NULL,
                generated_at DATETIME NOT NULL,
                last_updated DATETIME NOT NULL,
                ai_model_version VARCHAR(50) NOT NULL,
                project_id INTEGER NOT NULL UNIQUE REFERENCES main_project(id)
            );
        ''')
        print('Essential tables created manually')
"

# Show migration status
echo "Migration status:"
python manage.py showmigrations

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@nexora.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Verify database tables exist
echo "Verifying database tables..."
python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
tables = cursor.fetchall()
print('Database tables:', [table[0] for table in tables])
"

# Import data if export file exists
echo "Checking for data export file..."
if [ -f "nexora_data_export.json" ]; then
    echo "Found data export file, importing data..."
    python manage.py add_projects --input-file nexora_data_export.json || echo "Data import failed, continuing..."
else
    echo "No data export file found, generating AI analysis for existing projects..."
    python manage.py generate_ai_analysis --force || echo "AI analysis generation failed, continuing..."
fi

echo "Build complete!"
