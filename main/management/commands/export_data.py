"""
Management command to export all data from local database
This creates a JSON file with all projects, users, and AI analysis data
"""

from django.core.management.base import BaseCommand
from django.core import serializers
from main.models import Project, User, AIAnalystReport, UserProfile, Position, Application, Transaction, Message, Chat, MentorshipChat, DirectMessage, Notification, ProjectView, Investment, UserProjectAnalytics, Recommendation
import json
import os

class Command(BaseCommand):
    help = 'Export all data from local database to JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-file',
            type=str,
            default='nexora_data_export.json',
            help='Output file name for the exported data'
        )

    def handle(self, *args, **options):
        output_file = options['output_file']
        
        self.stdout.write('📤 Exporting all data from local database...')
        
        try:
            # Export all models
            data = {}
            
            # Export users first (required for foreign keys)
            self.stdout.write('  Exporting users...')
            data['users'] = serializers.serialize('json', User.objects.all())
            
            # Export user profiles
            self.stdout.write('  Exporting user profiles...')
            data['user_profiles'] = serializers.serialize('json', UserProfile.objects.all())
            
            # Export projects
            self.stdout.write('  Exporting projects...')
            data['projects'] = serializers.serialize('json', Project.objects.all())
            
            # Export AI analysis reports
            self.stdout.write('  Exporting AI analysis reports...')
            data['ai_analyst_reports'] = serializers.serialize('json', AIAnalystReport.objects.all())
            
            # Export positions
            self.stdout.write('  Exporting positions...')
            data['positions'] = serializers.serialize('json', Position.objects.all())
            
            # Export applications
            self.stdout.write('  Exporting applications...')
            data['applications'] = serializers.serialize('json', Application.objects.all())
            
            # Export transactions
            self.stdout.write('  Exporting transactions...')
            data['transactions'] = serializers.serialize('json', Transaction.objects.all())
            
            # Export messages
            self.stdout.write('  Exporting messages...')
            data['messages'] = serializers.serialize('json', Message.objects.all())
            
            # Export chats
            self.stdout.write('  Exporting chats...')
            data['chats'] = serializers.serialize('json', Chat.objects.all())
            
            # Export mentorship chats
            self.stdout.write('  Exporting mentorship chats...')
            data['mentorship_chats'] = serializers.serialize('json', MentorshipChat.objects.all())
            
            # Export direct messages
            self.stdout.write('  Exporting direct messages...')
            data['direct_messages'] = serializers.serialize('json', DirectMessage.objects.all())
            
            # Export notifications
            self.stdout.write('  Exporting notifications...')
            data['notifications'] = serializers.serialize('json', Notification.objects.all())
            
            # Export project views
            self.stdout.write('  Exporting project views...')
            data['project_views'] = serializers.serialize('json', ProjectView.objects.all())
            
            # Export investments
            self.stdout.write('  Exporting investments...')
            data['investments'] = serializers.serialize('json', Investment.objects.all())
            
            # Export user project analytics
            self.stdout.write('  Exporting user project analytics...')
            data['user_project_analytics'] = serializers.serialize('json', UserProjectAnalytics.objects.all())
            
            # Export recommendations
            self.stdout.write('  Exporting recommendations...')
            data['recommendations'] = serializers.serialize('json', Recommendation.objects.all())
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Get counts
            project_count = Project.objects.count()
            user_count = User.objects.count()
            ai_report_count = AIAnalystReport.objects.count()
            
            self.stdout.write(f'✅ Export completed!')
            self.stdout.write(f'  📊 Exported {user_count} users')
            self.stdout.write(f'  📊 Exported {project_count} projects')
            self.stdout.write(f'  📊 Exported {ai_report_count} AI analysis reports')
            self.stdout.write(f'  📁 Data saved to: {output_file}')
            
            # Show file size
            file_size = os.path.getsize(output_file) / 1024 / 1024  # MB
            self.stdout.write(f'  📏 File size: {file_size:.2f} MB')
            
        except Exception as e:
            self.stdout.write(f'❌ Export failed: {str(e)}')
            raise e
