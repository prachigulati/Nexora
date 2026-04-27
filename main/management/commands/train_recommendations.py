"""
Generate recommendation system using collaborative filtering.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import models
from main.models import Project, Investment, ProjectView, Recommendation
from main.views import generate_enhanced_recommendations_for_user
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate recommendations for users using collaborative filtering'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate recommendations for specific user ID only',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Starting recommendation generation...')
        
        # Check if we have enough data
        user_count = User.objects.count()
        project_count = Project.objects.count()
        interaction_count = Investment.objects.count() + ProjectView.objects.count()
        
        self.stdout.write(f"📊 Current data statistics:")
        self.stdout.write(f"   - Users: {user_count}")
        self.stdout.write(f"   - Projects: {project_count}")
        self.stdout.write(f"   - Interactions: {interaction_count}")
        
        if user_count < 1 or project_count < 1:
            self.stdout.write(self.style.WARNING('⚠️ Insufficient data for recommendations.'))
            return
        
        # Generate recommendations
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                self.generate_user_recommendations(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ User with ID {options["user_id"]} not found'))
        else:
            self.generate_all_recommendations()
    
    def generate_user_recommendations(self, user):
        """Generate recommendations for a specific user"""
        self.stdout.write(f"🎯 Generating recommendations for user: {user.username}")
        
        try:
            generate_enhanced_recommendations_for_user(user)
            count = Recommendation.objects.filter(user=user).count()
            self.stdout.write(self.style.SUCCESS(f"✅ Generated {count} recommendations for {user.username}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to generate recommendations for {user.username}: {str(e)}"))
    
    def generate_all_recommendations(self):
        """Generate recommendations for all users"""
        self.stdout.write("🎯 Generating recommendations for all users...")
        
        users = User.objects.all()
        success_count = 0
        total_recs = 0
        
        for user in users:
            try:
                generate_enhanced_recommendations_for_user(user)
                count = Recommendation.objects.filter(user=user).count()
                total_recs += count
                success_count += 1
                    
            except Exception as e:
                logger.error(f"Error generating recommendations for user {user.id}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"❌ Error for user {user.username}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f"✅ Generated recommendations for {success_count}/{users.count()} users"))
        self.stdout.write(f"📊 Total recommendations created: {total_recs}")