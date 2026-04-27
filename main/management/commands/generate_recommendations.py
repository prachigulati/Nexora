"""
Django management command to generate recommendations using a simple collaborative filtering approach.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg, Q
from main.models import Project, Investment, ProjectView, Recommendation
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate recommendations using simple collaborative filtering'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate recommendations for specific user only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate all recommendations',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting recommendation generation...'))
        
        # Check current data
        total_users = User.objects.count()
        total_projects = Project.objects.count()
        total_investments = Investment.objects.count()
        total_views = ProjectView.objects.count()
        
        self.stdout.write(f"📊 Current data:")
        self.stdout.write(f"   Users: {total_users}")
        self.stdout.write(f"   Projects: {total_projects}")
        self.stdout.write(f"   Investments: {total_investments}")
        self.stdout.write(f"   Project Views: {total_views}")
        
        if options['user_id']:
            try:
                user = User.objects.get(id=options['user_id'])
                self.generate_user_recommendations(user, force=options['force'])
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ User with ID {options["user_id"]} not found'))
        else:
            self.generate_all_recommendations(force=options['force'])
    
    def generate_user_recommendations(self, user, force=False):
        """Generate recommendations for a specific user"""
        self.stdout.write(f"🎯 Generating recommendations for user: {user.username}")
        
        if force:
            Recommendation.objects.filter(user=user).delete()
        
        # Get user's interaction data
        user_investments = Investment.objects.filter(investor=user).values_list('project', flat=True)
        user_views = ProjectView.objects.filter(user=user).values_list('project', flat=True)
        user_created = Project.objects.filter(user=user).values_list('id', flat=True)
        
        self.stdout.write(f"   User investments: {len(user_investments)}")
        self.stdout.write(f"   User views: {len(user_views)}")
        self.stdout.write(f"   User created: {len(user_created)}")
        
        if not user_investments and not user_views:
            self.stdout.write(self.style.WARNING('⚠️ No interaction data for user. Creating popular project recommendations...'))
            self.create_popular_recommendations(user)
            return
        
        # Find similar users based on investment patterns
        similar_users = self.find_similar_users(user)
        self.stdout.write(f"   Found {len(similar_users)} similar users")
        
        if not similar_users:
            self.stdout.write(self.style.WARNING('⚠️ No similar users found. Creating popular project recommendations...'))
            self.create_popular_recommendations(user)
            return
        
        # Get projects that similar users invested in
        recommended_projects = self.get_recommended_projects(user, similar_users)
        self.stdout.write(f"   Found {len(recommended_projects)} potential recommendations")
        
        # Create recommendations
        created_count = 0
        for project, score in recommended_projects:
            # Skip only if user already invested in or created this project
            # Allow viewed projects to be recommended again
            if (project.id in user_investments or 
                project.id in user_created):
                continue
            
            # Calculate recommended amount
            recommended_amount = self.calculate_recommended_amount(user, project)
            
            # Create recommendation
            recommendation, created = Recommendation.objects.get_or_create(
                user=user,
                project=project,
                defaults={
                    'score': score,
                    'recommended_amount': recommended_amount,
                    'created_at': timezone.now()
                }
            )
            
            if created:
                created_count += 1
            elif force:
                # Update existing recommendation
                recommendation.score = score
                recommendation.recommended_amount = recommended_amount
                recommendation.save()
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"✅ Generated {created_count} recommendations for {user.username}"))
    
    def generate_all_recommendations(self, force=False):
        """Generate recommendations for all users"""
        self.stdout.write('🎯 Generating recommendations for all users...')
        
        users = User.objects.all()
        success_count = 0
        
        for user in users:
            try:
                self.generate_user_recommendations(user, force=force)
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error for {user.username}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f'🎉 Generated recommendations for {success_count}/{users.count()} users'))
    
    def find_similar_users(self, user):
        """Find users with similar investment patterns"""
        try:
            # Get user's invested projects
            user_investments = set(Investment.objects.filter(investor=user).values_list('project', flat=True))
            
            if not user_investments:
                return []
            
            # Find other users who invested in the same projects
            similar_users = []
            for project_id in user_investments:
                investors = Investment.objects.filter(project_id=project_id).exclude(investor=user).values_list('investor', flat=True)
                similar_users.extend(investors)
            
            # Count occurrences and return most similar users
            from collections import Counter
            user_counts = Counter(similar_users)
            
            # Return users with at least 1 common investment
            return [user_id for user_id, count in user_counts.most_common(10) if count > 0]
            
        except Exception as e:
            logger.error(f"Error finding similar users for {user.username}: {str(e)}")
            return []
    
    def get_recommended_projects(self, user, similar_users):
        """Get projects that similar users invested in"""
        try:
            # Get projects that similar users invested in
            recommended_projects = []
            
            for similar_user_id in similar_users:
                investments = Investment.objects.filter(investor_id=similar_user_id)
                
                for investment in investments:
                    # Calculate score based on investment amount and recency
                    score = self.calculate_project_score(investment.project, investment.amount, investment.timestamp)
                    recommended_projects.append((investment.project, score))
            
            # Remove duplicates and sort by score
            project_scores = {}
            for project, score in recommended_projects:
                if project.id not in project_scores or score > project_scores[project.id]:
                    project_scores[project.id] = (project, score)
            
            # Sort by score and return top recommendations
            sorted_projects = sorted(project_scores.values(), key=lambda x: x[1], reverse=True)
            return sorted_projects[:50]  # Top 50 recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommended projects for {user.username}: {str(e)}")
            return []
    
    def calculate_project_score(self, project, investment_amount, timestamp):
        """Calculate a score for a project based on investment data"""
        try:
            score = 0.0
            
            # Base score from investment amount (normalized)
            if investment_amount:
                score += min(1.0, float(investment_amount) / 10.0)  # Normalize to 0-1
            
            # Recency bonus (more recent investments get higher scores)
            days_ago = (timezone.now() - timestamp).days
            recency_bonus = max(0, 1.0 - (days_ago / 30.0))  # Decay over 30 days
            score += recency_bonus * 0.3
            
            # Project popularity bonus
            total_investments = Investment.objects.filter(project=project).count()
            popularity_bonus = min(1.0, total_investments / 10.0)  # Normalize to 0-1
            score += popularity_bonus * 0.2
            
            # Funding progress bonus
            if project.funding_goal > 0:
                current_funding = project.current_funding()
                funding_progress = min(1.0, current_funding / project.funding_goal)
                score += funding_progress * 0.2
            
            return min(1.0, score)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating project score: {str(e)}")
            return 0.5  # Default score
    
    def calculate_recommended_amount(self, user, project):
        """Calculate recommended investment amount for a user and project"""
        try:
            # Get user's average investment amount
            user_investments = Investment.objects.filter(investor=user)
            if user_investments.exists():
                avg_amount = user_investments.aggregate(avg=Avg('amount'))['avg']
                base_amount = float(avg_amount)
            else:
                base_amount = 1.0  # Default amount
            
            # Adjust based on project funding goal
            if project.funding_goal > 0:
                # Don't recommend more than 10% of funding goal
                max_amount = float(project.funding_goal) * 0.1
                base_amount = min(base_amount, max_amount)
            
            # Ensure minimum amount
            return max(0.1, base_amount)
            
        except Exception as e:
            logger.error(f"Error calculating recommended amount: {str(e)}")
            return 1.0  # Default amount
    
    def create_popular_recommendations(self, user):
        """Create recommendations based on popular projects when no interaction data exists"""
        try:
            # Get popular projects (most invested in)
            popular_projects = Project.objects.annotate(
                investment_count=Count('investment'),
                total_invested=Sum('investment__amount')
            ).filter(
                investment_count__gt=0
            ).order_by('-investment_count', '-total_invested')[:20]
            
            if not popular_projects.exists():
                # If no investments exist, get projects with most views
                popular_projects = Project.objects.annotate(
                    view_count=Count('projectview')
                ).filter(
                    view_count__gt=0
                ).order_by('-view_count')[:20]
            
            if not popular_projects.exists():
                # Fallback to all projects
                popular_projects = Project.objects.all()[:20]
            
            created_count = 0
            for i, project in enumerate(popular_projects):
                # Skip if user created this project
                if project.user == user:
                    continue
                
                # Calculate score (decreasing for popular projects)
                score = 1.0 - (i * 0.1)
                recommended_amount = self.calculate_recommended_amount(user, project)
                
                # Create recommendation
                recommendation, created = Recommendation.objects.get_or_create(
                    user=user,
                    project=project,
                    defaults={
                        'score': score,
                        'recommended_amount': recommended_amount,
                        'created_at': timezone.now()
                    }
                )
                
                if created:
                    created_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {created_count} popular project recommendations for {user.username}"))
            
        except Exception as e:
            logger.error(f"Error creating popular recommendations for {user.username}: {str(e)}")
            self.stdout.write(self.style.ERROR(f"❌ Error creating popular recommendations: {str(e)}"))
