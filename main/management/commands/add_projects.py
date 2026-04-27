from django.core.management.base import BaseCommand
from django.core import serializers
from django.db import transaction
from django.contrib.auth.models import User
from main.models import Project, UserProfile, AIAnalystReport
import json
import os

class Command(BaseCommand):
    help = 'Add projects from export file to existing database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input-file',
            type=str,
            default='nexora_data_export.json',
            help='Input file name for the imported data'
        )

    def handle(self, *args, **options):
        input_file = options['input_file']
        
        if not os.path.exists(input_file):
            self.stdout.write(f'❌ File not found: {input_file}')
            return
        
        self.stdout.write('📥 Adding projects to database...')
        
        try:
            # Load data from file
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            # Check current counts
            current_projects = Project.objects.count()
            current_users = User.objects.count()
            self.stdout.write(f'Current database: {current_users} users, {current_projects} projects')
            
            # Import users first (skip if they already exist)
            self.stdout.write('  Checking users...')
            imported_users = 0
            for obj in serializers.deserialize('json', data['users']):
                user = obj.object
                if not User.objects.filter(username=user.username).exists():
                    obj.save()
                    imported_users += 1
            
            if imported_users > 0:
                self.stdout.write(f'  Imported {imported_users} new users')
            else:
                self.stdout.write('  All users already exist')
            
            # Import user profiles
            self.stdout.write('  Checking user profiles...')
            imported_profiles = 0
            for obj in serializers.deserialize('json', data['user_profiles']):
                profile = obj.object
                if not UserProfile.objects.filter(user_id=profile.user_id).exists():
                    obj.save()
                    imported_profiles += 1
            
            if imported_profiles > 0:
                self.stdout.write(f'  Imported {imported_profiles} new user profiles')
            else:
                self.stdout.write('  All user profiles already exist')
            
            # Import projects
            self.stdout.write('  Checking projects...')
            imported_projects = 0
            for obj in serializers.deserialize('json', data['projects']):
                project = obj.object
                if not Project.objects.filter(name=project.name).exists():
                    obj.save()
                    imported_projects += 1
            
            if imported_projects > 0:
                self.stdout.write(f'  Imported {imported_projects} new projects')
            else:
                self.stdout.write('  All projects already exist')
            
            # Import AI analysis reports
            self.stdout.write('  Checking AI analysis reports...')
            imported_reports = 0
            for obj in serializers.deserialize('json', data['ai_analyst_reports']):
                report = obj.object
                if not AIAnalystReport.objects.filter(project_id=report.project_id).exists():
                    obj.save()
                    imported_reports += 1
            
            if imported_reports > 0:
                self.stdout.write(f'  Imported {imported_reports} new AI analysis reports')
            else:
                self.stdout.write('  All AI analysis reports already exist')
            
            # Show final summary
            final_projects = Project.objects.count()
            final_users = User.objects.count()
            self.stdout.write('✅ Import completed!')
            self.stdout.write(f'📊 Final database: {final_users} users, {final_projects} projects')
            
        except Exception as e:
            self.stdout.write(f'❌ Import failed: {e}')
            raise e
