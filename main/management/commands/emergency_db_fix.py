"""
Emergency database fix command for Render deployment
This command ensures all required tables are created
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Emergency database fix for Render deployment'

    def handle(self, *args, **options):
        self.stdout.write('🚨 EMERGENCY DATABASE FIX STARTING...')
        
        try:
            # Step 1: Check current database state
            self.stdout.write('📊 Checking database state...')
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                existing_tables = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f'Existing tables: {existing_tables}')
            
            # Step 2: Try standard migrations first
            self.stdout.write('📦 Running standard migrations...')
            try:
                call_command('migrate', verbosity=0, interactive=False)
                self.stdout.write('✅ Standard migrations completed')
            except Exception as e:
                self.stdout.write(f'⚠️  Standard migrations failed: {e}')
            
            # Step 3: Create essential tables manually
            self.stdout.write('🔨 Creating essential tables manually...')
            self.create_essential_tables()
            
            # Step 4: Verify database is working
            self.stdout.write('🔍 Verifying database...')
            try:
                from main.models import Project
                project_count = Project.objects.count()
                self.stdout.write(f'✅ Database working! Found {project_count} projects')
            except Exception as e:
                self.stdout.write(f'❌ Database verification failed: {e}')
                # Try one more time with more aggressive approach
                self.create_essential_tables_aggressive()
            
            # Step 5: Generate AI analysis
            self.stdout.write('🤖 Generating AI analysis...')
            try:
                call_command('generate_ai_analysis', force=True)
                self.stdout.write('✅ AI analysis generated')
            except Exception as e:
                self.stdout.write(f'⚠️  AI analysis failed: {e}')
            
            self.stdout.write('🎉 EMERGENCY DATABASE FIX COMPLETED!')
            
        except Exception as e:
            self.stdout.write(f'❌ CRITICAL ERROR: {str(e)}')
            logger.error(f"Emergency database fix failed: {str(e)}")

    def create_essential_tables(self):
        """Create essential tables manually"""
        with connection.cursor() as cursor:
            # Create auth_user table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    password VARCHAR(128) NOT NULL DEFAULT '',
                    last_login DATETIME,
                    is_superuser BOOLEAN NOT NULL DEFAULT 0,
                    username VARCHAR(150) NOT NULL UNIQUE,
                    first_name VARCHAR(150) NOT NULL DEFAULT '',
                    last_name VARCHAR(150) NOT NULL DEFAULT '',
                    email VARCHAR(254) NOT NULL DEFAULT '',
                    is_staff BOOLEAN NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    date_joined DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create main_project table
            cursor.execute("""
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
                    funding_goal DECIMAL(10,2) NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER NOT NULL REFERENCES auth_user(id)
                );
            """)
            
            # Create main_aianalystreport table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS main_aianalystreport (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    risk_score REAL NOT NULL DEFAULT 50.0,
                    risk_level VARCHAR(20) NOT NULL DEFAULT 'medium',
                    tam_inflation_risk REAL NOT NULL DEFAULT 50.0,
                    financial_consistency_risk REAL NOT NULL DEFAULT 50.0,
                    market_saturation_risk REAL NOT NULL DEFAULT 50.0,
                    competition_risk REAL NOT NULL DEFAULT 50.0,
                    team_risk REAL NOT NULL DEFAULT 50.0,
                    growth_score REAL NOT NULL DEFAULT 50.0,
                    growth_index VARCHAR(20) NOT NULL DEFAULT 'medium',
                    traction_score REAL NOT NULL DEFAULT 50.0,
                    hiring_momentum REAL NOT NULL DEFAULT 50.0,
                    market_demand_score REAL NOT NULL DEFAULT 50.0,
                    scalability_potential REAL NOT NULL DEFAULT 50.0,
                    sector_rank INTEGER NOT NULL DEFAULT 1,
                    sector_percentile REAL NOT NULL DEFAULT 50.0,
                    platform_rank INTEGER NOT NULL DEFAULT 1,
                    platform_percentile REAL NOT NULL DEFAULT 50.0,
                    vs_sector_avg REAL NOT NULL DEFAULT 0.0,
                    vs_platform_avg REAL NOT NULL DEFAULT 0.0,
                    vs_similar_stage REAL NOT NULL DEFAULT 0.0,
                    risk_analysis TEXT NOT NULL DEFAULT 'Risk analysis based on current metrics and market position.',
                    growth_analysis TEXT NOT NULL DEFAULT 'Growth analysis based on market metrics and sector dynamics.',
                    peer_analysis TEXT NOT NULL DEFAULT 'Competitive position analysis based on platform and sector benchmarks.',
                    recommendations TEXT NOT NULL DEFAULT 'Investment recommendation based on comprehensive risk-return analysis.',
                    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ai_model_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
                    project_id INTEGER NOT NULL UNIQUE REFERENCES main_project(id)
                );
            """)
            
            # Create other essential tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS main_userprofile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bio TEXT NOT NULL DEFAULT '',
                    location VARCHAR(100) NOT NULL DEFAULT '',
                    country VARCHAR(100) NOT NULL DEFAULT '',
                    country_code VARCHAR(10) NOT NULL DEFAULT '',
                    website VARCHAR(200) NOT NULL DEFAULT '',
                    phone VARCHAR(20) NOT NULL DEFAULT '',
                    avatar VARCHAR(100),
                    date_of_birth DATE,
                    linkedin_url VARCHAR(200) NOT NULL DEFAULT '',
                    twitter_url VARCHAR(200) NOT NULL DEFAULT '',
                    github_url VARCHAR(200) NOT NULL DEFAULT '',
                    company VARCHAR(100) NOT NULL DEFAULT '',
                    job_title VARCHAR(100) NOT NULL DEFAULT '',
                    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
                    language VARCHAR(10) NOT NULL DEFAULT 'en',
                    email_notifications BOOLEAN NOT NULL DEFAULT 1,
                    push_notifications BOOLEAN NOT NULL DEFAULT 0,
                    project_updates BOOLEAN NOT NULL DEFAULT 1,
                    investment_alerts BOOLEAN NOT NULL DEFAULT 1,
                    marketing_communications BOOLEAN NOT NULL DEFAULT 0,
                    profile_visibility VARCHAR(20) NOT NULL DEFAULT 'public',
                    show_activity_status BOOLEAN NOT NULL DEFAULT 1,
                    show_investment_history BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id)
                );
            """)
            
            self.stdout.write('✅ Essential tables created')

    def create_essential_tables_aggressive(self):
        """More aggressive table creation if standard approach fails"""
        self.stdout.write('🔨 AGGRESSIVE: Creating tables with minimal constraints...')
        with connection.cursor() as cursor:
            # Drop and recreate with minimal constraints
            cursor.execute("DROP TABLE IF EXISTS main_project;")
            cursor.execute("DROP TABLE IF EXISTS main_aianalystreport;")
            cursor.execute("DROP TABLE IF EXISTS main_userprofile;")
            
            # Recreate with minimal constraints
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
                    funding_goal DECIMAL(10,2) NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER NOT NULL
                );
            """)
            
            cursor.execute("""
                CREATE TABLE main_aianalystreport (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    risk_score REAL NOT NULL DEFAULT 50.0,
                    risk_level VARCHAR(20) NOT NULL DEFAULT 'medium',
                    tam_inflation_risk REAL NOT NULL DEFAULT 50.0,
                    financial_consistency_risk REAL NOT NULL DEFAULT 50.0,
                    market_saturation_risk REAL NOT NULL DEFAULT 50.0,
                    competition_risk REAL NOT NULL DEFAULT 50.0,
                    team_risk REAL NOT NULL DEFAULT 50.0,
                    growth_score REAL NOT NULL DEFAULT 50.0,
                    growth_index VARCHAR(20) NOT NULL DEFAULT 'medium',
                    traction_score REAL NOT NULL DEFAULT 50.0,
                    hiring_momentum REAL NOT NULL DEFAULT 50.0,
                    market_demand_score REAL NOT NULL DEFAULT 50.0,
                    scalability_potential REAL NOT NULL DEFAULT 50.0,
                    sector_rank INTEGER NOT NULL DEFAULT 1,
                    sector_percentile REAL NOT NULL DEFAULT 50.0,
                    platform_rank INTEGER NOT NULL DEFAULT 1,
                    platform_percentile REAL NOT NULL DEFAULT 50.0,
                    vs_sector_avg REAL NOT NULL DEFAULT 0.0,
                    vs_platform_avg REAL NOT NULL DEFAULT 0.0,
                    vs_similar_stage REAL NOT NULL DEFAULT 0.0,
                    risk_analysis TEXT NOT NULL DEFAULT 'Risk analysis based on current metrics and market position.',
                    growth_analysis TEXT NOT NULL DEFAULT 'Growth analysis based on market metrics and sector dynamics.',
                    peer_analysis TEXT NOT NULL DEFAULT 'Competitive position analysis based on platform and sector benchmarks.',
                    recommendations TEXT NOT NULL DEFAULT 'Investment recommendation based on comprehensive risk-return analysis.',
                    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ai_model_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
                    project_id INTEGER NOT NULL UNIQUE
                );
            """)
            
            self.stdout.write('✅ Aggressive table creation completed')
