"""
Django signals for real-time LightFM updates.
These signals trigger when users interact with projects.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from main.models import Project, ProjectView, Investment, Recommendation
import threading
import time

logger = logging.getLogger(__name__)

# Cache keys for tracking updates
LAST_UPDATE_KEY = 'recommendation_last_update'
UPDATE_COUNT_KEY = 'recommendation_update_count'
MIN_UPDATE_INTERVAL = 300  # 5 minutes minimum between updates


@receiver(post_save, sender=ProjectView)
def handle_project_view(sender, instance, created, **kwargs):
    """Handle new project views"""
    if created:
        logger.info(f"New project view: User {instance.user.id} viewed project {instance.project.id}")
        _schedule_user_update(instance.user)


@receiver(post_save, sender=Investment)
def handle_investment(sender, instance, created, **kwargs):
    """Handle new investments"""
    if created:
        logger.info(f"New investment: User {instance.investor.id} invested in project {instance.project.id}")
        _schedule_user_update(instance.investor)


@receiver(post_save, sender=Project)
def handle_new_project(sender, instance, created, **kwargs):
    """Handle new projects"""
    if created:
        logger.info(f"New project created: {instance.name}")
        _schedule_global_update()
        _schedule_ai_analysis(instance)


@receiver(post_delete, sender=Project)
def handle_project_deletion(sender, instance, **kwargs):
    """Handle project deletions"""
    logger.info(f"Project deleted: {instance.name}")
    _schedule_global_update()


@receiver(post_delete, sender=Investment)
def handle_investment_deletion(sender, instance, **kwargs):
    """Handle investment deletions"""
    logger.info(f"Investment deleted: User {instance.investor.id} for project {instance.project.id}")
    _schedule_user_update(instance.investor)


def _schedule_user_update(user):
    """Schedule a user-specific recommendation update"""
    try:
        # Use threading to avoid blocking the request
        thread = threading.Thread(
            target=_update_user_recommendations_async,
            args=(user.id,)
        )
        thread.daemon = True
        thread.start()
    except Exception as e:
        logger.error(f"Error scheduling user update: {str(e)}")


def _schedule_global_update():
    """Schedule a global model update"""
    try:
        # Check if we should update based on frequency
        last_update = cache.get(LAST_UPDATE_KEY)
        current_time = time.time()
        
        if last_update is None or (current_time - last_update) > MIN_UPDATE_INTERVAL:
            # Use threading to avoid blocking
            thread = threading.Thread(target=_update_global_recommendations_async)
            thread.daemon = True
            thread.start()
            
            # Update cache
            cache.set(LAST_UPDATE_KEY, current_time, 3600)  # 1 hour cache
        else:
            # Increment update counter
            update_count = cache.get(UPDATE_COUNT_KEY, 0) + 1
            cache.set(UPDATE_COUNT_KEY, update_count, 3600)
            
    except Exception as e:
        logger.error(f"Error scheduling global update: {str(e)}")


def _schedule_ai_analysis(project):
    """Schedule AI analysis generation for a new project"""
    try:
        # Use threading to avoid blocking the request
        thread = threading.Thread(
            target=_generate_ai_analysis_async,
            args=(project.id,)
        )
        thread.daemon = True
        thread.start()
        logger.info(f"Scheduled AI analysis for project: {project.name}")
    except Exception as e:
        logger.error(f"Error scheduling AI analysis for project {project.id}: {str(e)}")


def _update_user_recommendations_async(user_id):
    """Update recommendations for a specific user (async)"""
    try:
        user = User.objects.get(id=user_id)
        # Use the simple recommendation system
        from main.views import generate_enhanced_recommendations_for_user
        generate_enhanced_recommendations_for_user(user)
        
        logger.info(f"Updated recommendations for user {user.username}")
        success = True
        
        if success:
            logger.info(f"Updated recommendations for user {user.username}")
        else:
            logger.warning(f"No recommendations updated for user {user.username}")
            
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found for recommendation update")
    except Exception as e:
        logger.error(f"Error updating recommendations for user {user_id}: {str(e)}")


def _update_global_recommendations_async():
    """Update recommendations for all users (async)"""
    try:
        from main.views import generate_enhanced_recommendations_for_user
        
        logger.info("Starting global recommendation update...")
        
        # Update recommendations for all users
        users = User.objects.all()
        updated_count = 0
        
        for user in users:
            try:
                generate_enhanced_recommendations_for_user(user)
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating user {user.username}: {str(e)}")
        
        logger.info(f"Updated recommendations for {updated_count}/{users.count()} users")
            
    except Exception as e:
        logger.error(f"Error in global recommendation update: {str(e)}")


def _generate_ai_analysis_async(project_id):
    """Generate AI analysis for a project (async)"""
    try:
        from main.models import Project, AIAnalystReport
        from main.ai_analyst import ai_analyst
        
        project = Project.objects.get(id=project_id)
        
        # Check if analysis already exists
        if AIAnalystReport.objects.filter(project=project).exists():
            logger.info(f"AI analysis already exists for project: {project.name}")
            return
        
        # Generate AI analysis
        logger.info(f"Generating AI analysis for project: {project.name}")
        report = ai_analyst.generate_report(project)
        logger.info(f"AI analysis generated for project: {project.name} (Risk: {report.risk_level}, Growth: {report.growth_index})")
        
    except Project.DoesNotExist:
        logger.warning(f"Project {project_id} not found for AI analysis")
    except Exception as e:
        logger.error(f"Error generating AI analysis for project {project_id}: {str(e)}")


def get_recommendation_cache_key(user_id):
    """Get cache key for user recommendations"""
    return f"user_recommendations_{user_id}"


def cache_user_recommendations(user_id, recommendations, timeout=3600):
    """Cache user recommendations"""
    try:
        cache_key = get_recommendation_cache_key(user_id)
        cache.set(cache_key, recommendations, timeout)
        logger.info(f"Cached recommendations for user {user_id}")
    except Exception as e:
        logger.error(f"Error caching recommendations for user {user_id}: {str(e)}")


def get_cached_recommendations(user_id):
    """Get cached recommendations for user"""
    try:
        cache_key = get_recommendation_cache_key(user_id)
        return cache.get(cache_key)
    except Exception as e:
        logger.error(f"Error getting cached recommendations for user {user_id}: {str(e)}")
        return None


def invalidate_user_cache(user_id):
    """Invalidate user recommendation cache"""
    try:
        cache_key = get_recommendation_cache_key(user_id)
        cache.delete(cache_key)
        logger.info(f"Invalidated cache for user {user_id}")
    except Exception as e:
        logger.error(f"Error invalidating cache for user {user_id}: {str(e)}")


# Optional: Celery task for background processing
def schedule_recommendation_update_task():
    """Schedule a Celery task for recommendation updates"""
    try:
        # If Celery is available, use it for background processing
        from celery import shared_task
        
        @shared_task
        def update_recommendation_task():
            """Celery task for recommendation updates"""
            try:
                from main.views import generate_enhanced_recommendations_for_user
                from django.contrib.auth.models import User
                
                # Update all users
                users = User.objects.all()
                updated_count = 0
                for user in users:
                    try:
                        generate_enhanced_recommendations_for_user(user)
                        updated_count += 1
                    except Exception as e:
                        logger.error(f"Error updating user {user.username}: {str(e)}")
                
                logger.info(f"✅ Celery task completed recommendation update for {updated_count} users")
                    
            except Exception as e:
                logger.error(f"Error in Celery recommendation task: {str(e)}")
        
        # Schedule the task
        update_recommendation_task.delay()
        logger.info("✅ Scheduled Celery task for recommendation update")
        
    except ImportError:
        logger.info("Celery not available, using threading for background updates")
    except Exception as e:
        logger.error(f"Error scheduling Celery task: {str(e)}") 