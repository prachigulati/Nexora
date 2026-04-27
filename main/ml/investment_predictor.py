"""
AI Investment Predictor
Predicts personalized investment amounts based on project and user factors.
"""

from django.db.models import Sum, Avg, Count
from django.contrib.auth.models import User
from main.models import Project, ProjectView, Investment, UserProjectAnalytics
import logging

logger = logging.getLogger(__name__)


def predict_investment_amount(user, project):
    """
    Returns a personalized ETH amount the user should invest in a given project.
    
    Args:
        user: Django User object
        project: Project object
        
    Returns:
        float: Predicted investment amount in ETH
    """
    try:
        # 1. Project Stats
        total_views = ProjectView.objects.filter(project=project).aggregate(
            Sum('view_count')
        )['view_count__sum'] or 0
        
        total_investors = Investment.objects.filter(project=project).values('investor').distinct().count()
        
        avg_project_investment = Investment.objects.filter(project=project).aggregate(
            Avg('amount')
        )['amount__avg'] or 0
        
        funding_goal = project.funding_goal or 0
        total_raised = Investment.objects.filter(project=project).aggregate(
            Sum('amount')
        )['amount__sum'] or 0
        
        # 2. User Stats
        user_total_invested = Investment.objects.filter(investor=user).aggregate(
            Sum('amount')
        )['amount__sum'] or 0
        
        user_total_projects = Investment.objects.filter(investor=user).values('project').distinct().count()
        user_avg_invest = user_total_invested / user_total_projects if user_total_projects else avg_project_investment
        
        # User's time spent on this specific project
        user_project_view = ProjectView.objects.filter(user=user, project=project).first()
        time_spent = user_project_view.total_time_spent if user_project_view else 0
        
        # User's category preferences
        user_category_investments = Investment.objects.filter(investor=user).select_related('project')
        user_categories = [inv.project.category for inv in user_category_investments if inv.project.category]
        category_match = 1.0
        if user_categories and project.category:
            category_match = 1.2 if project.category in user_categories else 0.8
        
        # 3. AI-Inspired Logic (heuristic model)
        # Convert Decimal to float for calculations
        avg_project_investment_float = float(avg_project_investment)
        user_avg_invest_float = float(user_avg_invest)
        user_total_invested_float = float(user_total_invested)
        funding_goal_float = float(funding_goal)
        total_raised_float = float(total_raised)
        
        base_amount = (avg_project_investment_float + user_avg_invest_float) / 2
        
        # Adjust for project momentum and popularity
        popularity_factor = (total_views + total_investors * 2) / 10
        
        # Funding urgency factor
        funding_gap = funding_goal_float - total_raised_float
        funding_progress = (total_raised_float / funding_goal_float * 100) if funding_goal_float > 0 else 0
        
        # Urgency bonus for projects close to funding goal
        urgency_bonus = 1.3 if funding_progress > 70 else 1.0
        
        # Adjust for user engagement with this project
        time_weight = min(time_spent / 30, 1.5)  # boost if they spent 30+ seconds
        
        # User spending pattern adjustment
        user_spending_pattern = 1.0
        if user_total_invested_float > 0:
            # High spender bonus
            if user_total_invested_float > 1000:  # More than 1000 ETH total
                user_spending_pattern = 1.2
            # Low spender adjustment
            elif user_total_invested_float < 100:  # Less than 100 ETH total
                user_spending_pattern = 0.8
        
        # Category preference adjustment
        category_bonus = category_match
        
        # Final predicted ETH with all factors
        predicted_amount = (
            base_amount * 
            time_weight * 
            urgency_bonus * 
            user_spending_pattern * 
            category_bonus + 
            popularity_factor
        )
        
        # Ensure minimum investment amount
        min_investment = 0.1  # Minimum 0.1 ETH
        predicted_amount = max(predicted_amount, min_investment)
        
        # Cap suggested amount to avoid over-suggesting
        max_suggestion = funding_gap if funding_gap > 0 else 10.0  # Cap at funding gap or 10 ETH
        predicted_amount = min(predicted_amount, max_suggestion)
        
        return round(predicted_amount, 2)
        
    except Exception as e:
        logger.error(f"Error predicting investment amount for user {user.id} and project {project.id}: {str(e)}")
        # Fallback to average project investment
        avg_investment = Investment.objects.filter(project=project).aggregate(
            Avg('amount')
        )['amount__avg'] or 1.0
        return round(avg_investment, 2)


def get_project_analytics(project):
    """
    Get comprehensive analytics for a project.
    
    Args:
        project: Project object
        
    Returns:
        dict: Project analytics
    """
    try:
        total_views = ProjectView.objects.filter(project=project).aggregate(
            Sum('view_count')
        )['view_count__sum'] or 0
        
        total_investors = Investment.objects.filter(project=project).values('investor').distinct().count()
        
        avg_investment = Investment.objects.filter(project=project).aggregate(
            Avg('amount')
        )['amount__avg'] or 0
        
        total_raised = Investment.objects.filter(project=project).aggregate(
            Sum('amount')
        )['amount__sum'] or 0
        
        funding_progress = (total_raised / project.funding_goal * 100) if project.funding_goal > 0 else 0
        
        return {
            'total_views': total_views,
            'total_investors': total_investors,
            'avg_investment': round(avg_investment, 2),
            'total_raised': round(total_raised, 2),
            'funding_progress': round(funding_progress, 1),
            'funding_goal': project.funding_goal or 0
        }
        
    except Exception as e:
        logger.error(f"Error getting project analytics for project {project.id}: {str(e)}")
        return {}


def get_user_investment_profile(user):
    """
    Get comprehensive investment profile for a user.
    
    Args:
        user: Django User object
        
    Returns:
        dict: User investment profile
    """
    try:
        user_investments = Investment.objects.filter(investor=user)
        
        total_invested = user_investments.aggregate(Sum('amount'))['amount__sum'] or 0
        total_projects = user_investments.values('project').distinct().count()
        avg_per_project = total_invested / total_projects if total_projects > 0 else 0
        
        # Category preferences
        category_investments = user_investments.select_related('project')
        categories = {}
        for inv in category_investments:
            if inv.project.category:
                categories[inv.project.category] = categories.get(inv.project.category, 0) + 1
        
        # Spending pattern classification
        spending_pattern = 'low'
        if total_invested > 1000:
            spending_pattern = 'high'
        elif total_invested > 100:
            spending_pattern = 'medium'
        
        return {
            'total_invested': round(total_invested, 2),
            'total_projects': total_projects,
            'avg_per_project': round(avg_per_project, 2),
            'categories': categories,
            'spending_pattern': spending_pattern
        }
        
    except Exception as e:
        logger.error(f"Error getting user investment profile for user {user.id}: {str(e)}")
        return {}


def predict_investment_with_explanation(user, project):
    """
    Returns predicted investment amount with explanation of factors.
    
    Args:
        user: Django User object
        project: Project object
        
    Returns:
        dict: Prediction with explanation
    """
    try:
        predicted_amount = predict_investment_amount(user, project)
        project_analytics = get_project_analytics(project)
        user_profile = get_user_investment_profile(user)
        
        # Generate explanation
        explanations = []
        
        if project_analytics.get('total_investors', 0) > 5:
            explanations.append(f"Popular project with {project_analytics['total_investors']} investors")
        
        if project_analytics.get('funding_progress', 0) > 70:
            explanations.append("Project is close to funding goal")
        
        if user_profile.get('spending_pattern') == 'high':
            explanations.append("Based on your high investment history")
        elif user_profile.get('spending_pattern') == 'low':
            explanations.append("Conservative amount based on your investment pattern")
        
        # Check category preference
        user_categories = user_profile.get('categories', {})
        if project.category and project.category in user_categories:
            explanations.append(f"You've invested in {project.category} projects before")
        
        return {
            'predicted_amount': predicted_amount,
            'project_analytics': project_analytics,
            'user_profile': user_profile,
            'explanations': explanations
        }
        
    except Exception as e:
        logger.error(f"Error predicting investment with explanation: {str(e)}")
        return {
            'predicted_amount': 1.0,
            'project_analytics': {},
            'user_profile': {},
            'explanations': ['Using default recommendation']
        } 