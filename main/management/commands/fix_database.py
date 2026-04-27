"""
Management command to fix database issues and ensure all migrations are applied.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix database issues and ensure all migrations are applied'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check database status without making changes',
        )

    def handle(self, *args, **options):
        check_only = options['check_only']
        
        self.stdout.write('🔍 Checking database status...')
        
        # Check if database tables exist
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('main_project', 'auth_user', 'main_aianalystreport')
                ORDER BY name
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
        
        self.stdout.write(f'Existing tables: {existing_tables}')
        
        missing_tables = []
        required_tables = ['main_project', 'auth_user', 'main_aianalystreport']
        
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            self.stdout.write(
                self.style.WARNING(f'Missing tables: {missing_tables}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ All required tables exist')
            )
        
        if check_only:
            return
        
        if missing_tables:
            self.stdout.write('\n🔧 Fixing database issues...')
            
            try:
                # Run migrations
                self.stdout.write('Running migrations...')
                call_command('migrate', verbosity=2, interactive=False)
                
                # Check again
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name IN ('main_project', 'auth_user', 'main_aianalystreport')
                        ORDER BY name
                    """)
                    existing_tables_after = [row[0] for row in cursor.fetchall()]
                
                still_missing = []
                for table in required_tables:
                    if table not in existing_tables_after:
                        still_missing.append(table)
                
                if still_missing:
                    self.stdout.write(
                        self.style.ERROR(f'Still missing tables after migration: {still_missing}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✅ All tables created successfully!')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error running migrations: {str(e)}')
                )
                logger.error(f"Error running migrations: {str(e)}")
        else:
            self.stdout.write('✅ Database is already in good state')
        
        # Check for any pending migrations
        try:
            self.stdout.write('\n🔍 Checking for pending migrations...')
            call_command('showmigrations', verbosity=0)
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not check migrations: {str(e)}')
            )
