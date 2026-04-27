from django.core.management.base import BaseCommand
from django.core import serializers
from django.db import transaction
from django.contrib.auth.models import User
from main.models import Project, UserProfile, Position, Application, Transaction, Message, Chat, MentorshipChat, DirectMessage, Notification, ProjectView, Investment, UserProjectAnalytics, Recommendation, AIAnalystReport
import json
import os

class Command(BaseCommand):
    help = 'Simple import command that handles the current export format correctly.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input-file',
            type=str,
            default='nexora_data_export.json',
            help='Input file name for the imported data'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear all existing data before importing.'
        )

    def handle(self, *args, **options):
        input_file = options['input_file']
        clear_existing = options['clear_existing']
        
        if not os.path.exists(input_file):
            self.stdout.write(f'❌ File not found: {input_file}')
            return
        
        self.stdout.write('📥 Importing data into database...')
        
        try:
            # Load data from file
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            if clear_existing:
                self.stdout.write('🗑️  Clearing existing data...')
                # Clear in reverse order to avoid foreign key constraints
                Recommendation.objects.all().delete()
                UserProjectAnalytics.objects.all().delete()
                Investment.objects.all().delete()
                ProjectView.objects.all().delete()
                Notification.objects.all().delete()
                DirectMessage.objects.all().delete()
                MentorshipChat.objects.all().delete()
                Chat.objects.all().delete()
                Message.objects.all().delete()
                Transaction.objects.all().delete()
                Application.objects.all().delete()
                Position.objects.all().delete()
                AIAnalystReport.objects.all().delete()
                Project.objects.all().delete()
                # Delete all UserProfiles first
                UserProfile.objects.all().delete()
                # Keep superusers, delete regular users
                User.objects.exclude(is_superuser=True).delete()
            
            # Import users first (required for foreign keys)
            self.stdout.write('  Importing users...')
            for obj in serializers.deserialize('json', data['users']):
                obj.save()
            
            # Import user profiles
            self.stdout.write('  Importing user profiles...')
            for obj in serializers.deserialize('json', data['user_profiles']):
                obj.save()
            
            # Import projects
            self.stdout.write('  Importing projects...')
            for obj in serializers.deserialize('json', data['projects']):
                obj.save()
            
            # Import AI analysis reports
            self.stdout.write('  Importing AI analysis reports...')
            for obj in serializers.deserialize('json', data['ai_analyst_reports']):
                obj.save()
            
            # Import positions
            self.stdout.write('  Importing positions...')
            for obj in serializers.deserialize('json', data['positions']):
                obj.save()
            
            # Import applications
            self.stdout.write('  Importing applications...')
            for obj in serializers.deserialize('json', data['applications']):
                obj.save()
            
            # Import transactions
            self.stdout.write('  Importing transactions...')
            for obj in serializers.deserialize('json', data['transactions']):
                obj.save()
            
            # Import messages
            self.stdout.write('  Importing messages...')
            for obj in serializers.deserialize('json', data['messages']):
                obj.save()
            
            # Import chats
            self.stdout.write('  Importing chats...')
            for obj in serializers.deserialize('json', data['chats']):
                obj.save()
            
            # Import mentorship chats
            self.stdout.write('  Importing mentorship chats...')
            for obj in serializers.deserialize('json', data['mentorship_chats']):
                obj.save()
            
            # Import direct messages
            self.stdout.write('  Importing direct messages...')
            for obj in serializers.deserialize('json', data['direct_messages']):
                obj.save()
            
            # Import notifications
            self.stdout.write('  Importing notifications...')
            for obj in serializers.deserialize('json', data['notifications']):
                obj.save()
            
            # Import project views
            self.stdout.write('  Importing project views...')
            for obj in serializers.deserialize('json', data['project_views']):
                obj.save()
            
            # Import investments
            self.stdout.write('  Importing investments...')
            for obj in serializers.deserialize('json', data['investments']):
                obj.save()
            
            # Import user project analytics
            self.stdout.write('  Importing user project analytics...')
            for obj in serializers.deserialize('json', data['user_project_analytics']):
                obj.save()
            
            # Import recommendations
            self.stdout.write('  Importing recommendations...')
            for obj in serializers.deserialize('json', data['recommendations']):
                obj.save()
            
            self.stdout.write('✅ Data successfully imported!')
            
            # Show summary
            self.stdout.write(f'📊 Imported {User.objects.count()} users')
            self.stdout.write(f'📊 Imported {Project.objects.count()} projects')
            self.stdout.write(f'📊 Imported {AIAnalystReport.objects.count()} AI analysis reports')
            
        except Exception as e:
            self.stdout.write(f'❌ Import failed: {e}')
            raise e
