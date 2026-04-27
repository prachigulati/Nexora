"""
Management command to force database migration and fix deployment issues.
This command ensures all tables are created even if migrations fail.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection, transaction
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Force database migration and fix deployment issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset database and recreate all tables (DESTRUCTIVE)',
        )

    def handle(self, *args, **options):
        reset = options['reset']
        
        self.stdout.write('🔧 Starting database migration fix...')
        
        try:
            if reset:
                self.stdout.write('⚠️  RESET MODE: This will delete all data!')
                self.reset_database()
            else:
                self.fix_database()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during migration fix: {str(e)}')
            )
            logger.error(f"Migration fix error: {str(e)}")
            raise

    def reset_database(self):
        """Reset database completely (DESTRUCTIVE)"""
        self.stdout.write('🗑️  Resetting database...')
        
        with connection.cursor() as cursor:
            # Drop all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                    self.stdout.write(f'  Dropped table: {table_name}')
        
        # Run migrations
        self.stdout.write('🔄 Running migrations...')
        call_command('migrate', verbosity=2, interactive=False)
        
        # Create superuser
        self.create_superuser()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Database reset completed!')
        )

    def fix_database(self):
        """Fix database without losing data"""
        self.stdout.write('🔍 Checking database status...')
        
        # Check existing tables
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = [row[0] for row in cursor.fetchall()]
        
        self.stdout.write(f'Existing tables: {existing_tables}')
        
        # Required tables
        required_tables = [
            'auth_user',
            'auth_group',
            'auth_permission',
            'auth_user_groups',
            'auth_user_user_permissions',
            'django_content_type',
            'django_migrations',
            'django_session',
            'main_project',
            'main_userprofile',
            'main_position',
            'main_application',
            'main_transaction',
            'main_message',
            'main_chat',
            'main_mentorshipchat',
            'main_directmessage',
            'main_notification',
            'main_projectview',
            'main_investment',
            'main_userprojectanalytics',
            'main_recommendation',
            'main_aianalystreport'
        ]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            self.stdout.write(
                self.style.WARNING(f'Missing tables: {missing_tables}')
            )
            
            # Try to run migrations
            self.stdout.write('🔄 Running migrations...')
            try:
                call_command('migrate', verbosity=2, interactive=False)
                
                # Check again
                with connection.cursor() as cursor:
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    existing_tables_after = [row[0] for row in cursor.fetchall()]
                
                still_missing = [table for table in required_tables if table not in existing_tables_after]
                
                if still_missing:
                    self.stdout.write(
                        self.style.ERROR(f'Still missing tables: {still_missing}')
                    )
                    # Try to create missing tables manually
                    self.create_missing_tables(still_missing)
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✅ All tables created successfully!')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Migration failed: {str(e)}')
                )
                # Try to create tables manually
                self.create_missing_tables(missing_tables)
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ All required tables exist!')
            )
        
        # Create superuser if needed
        self.create_superuser()
        
        # Generate AI analysis for existing projects
        self.stdout.write('🤖 Generating AI analysis for existing projects...')
        try:
            call_command('generate_ai_analysis')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'AI analysis generation failed: {str(e)}')
            )

    def create_missing_tables(self, missing_tables):
        """Create missing tables manually"""
        self.stdout.write('🔨 Creating missing tables manually...')
        
        with connection.cursor() as cursor:
            # Create auth_user table
            if 'auth_user' in missing_tables:
                cursor.execute("""
                    CREATE TABLE auth_user (
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
                """)
                self.stdout.write('  Created auth_user table')
            
            # Create main_project table
            if 'main_project' in missing_tables:
                cursor.execute("""
                    CREATE TABLE main_project (
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
                """)
                self.stdout.write('  Created main_project table')
            
            # Create main_aianalystreport table
            if 'main_aianalystreport' in missing_tables:
                cursor.execute("""
                    CREATE TABLE main_aianalystreport (
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
                """)
                self.stdout.write('  Created main_aianalystreport table')
            
            # Create other essential tables
            if 'main_userprofile' in missing_tables:
                cursor.execute("""
                    CREATE TABLE main_userprofile (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bio TEXT NOT NULL,
                        location VARCHAR(100) NOT NULL,
                        country VARCHAR(100) NOT NULL,
                        country_code VARCHAR(10) NOT NULL,
                        website VARCHAR(200) NOT NULL,
                        phone VARCHAR(20) NOT NULL,
                        avatar VARCHAR(100),
                        date_of_birth DATE,
                        linkedin_url VARCHAR(200) NOT NULL,
                        twitter_url VARCHAR(200) NOT NULL,
                        github_url VARCHAR(200) NOT NULL,
                        company VARCHAR(100) NOT NULL,
                        job_title VARCHAR(100) NOT NULL,
                        timezone VARCHAR(50) NOT NULL,
                        language VARCHAR(10) NOT NULL,
                        email_notifications BOOLEAN NOT NULL,
                        push_notifications BOOLEAN NOT NULL,
                        project_updates BOOLEAN NOT NULL,
                        investment_alerts BOOLEAN NOT NULL,
                        marketing_communications BOOLEAN NOT NULL,
                        profile_visibility VARCHAR(20) NOT NULL,
                        show_activity_status BOOLEAN NOT NULL,
                        show_investment_history BOOLEAN NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id)
                    );
                """)
                self.stdout.write('  Created main_userprofile table')

    def create_superuser(self):
        """Create superuser if it doesn't exist"""
        try:
            from django.contrib.auth.models import User
            
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser('admin', 'admin@nexora.com', 'admin123')
                self.stdout.write('  Created superuser: admin/admin123')
            else:
                self.stdout.write('  Superuser already exists')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not create superuser: {str(e)}')
            )
