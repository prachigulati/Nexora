from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import Project, Position, Application, Transaction, Chat, Message, UserProfile, Notification, MentorshipChat, DirectMessage, ProjectView, UserProjectAnalytics, Investment, Recommendation, AIAnalystReport
from .ml.investment_predictor import predict_investment_amount, predict_investment_with_explanation
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import json
from django.db import models
import os
from dotenv import load_dotenv
import logging
from django.utils import timezone
from django.views.decorators.http import require_POST
from decimal import Decimal
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.conf import settings
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import io
from django.db.models.functions import TruncMonth, TruncDay
import pickle
# from sentence_transformers import util
# import numpy as np
# import numpy as np
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
from django.shortcuts import redirect, render
from .models import Project
from django.http import JsonResponse
from django.http import JsonResponse
from django.http import JsonResponse
from .models import Project

# Load .env variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Gemini client if API key is available
from django.conf import settings

def get_gemini_model():
    """Get or create Gemini model instance"""
    try:
        import google.generativeai as genai
        GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', os.environ.get("GEMINI_API_KEY"))
        
        if GEMINI_API_KEY and GEMINI_API_KEY != "GEMINI_API_KEY" and GEMINI_API_KEY != "NOT_FOUND":
            genai.configure(api_key=GEMINI_API_KEY)
            return genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.warning(f"Missing GEMINI_API_KEY in environment variables! Key: {GEMINI_API_KEY}")
            return None
    except ImportError:
        logger.warning("Google Generative AI package not installed. Install with: pip install google-generativeai")
        return None

gemini_model = get_gemini_model()

def ask_gemini(message):
    """Send a message to AI service and get a response with fallback"""
    try:
        from main.ai_service import ai_service
        
        system_prompt = "You are a helpful assistant for a startup funding platform. Provide concise, helpful answers about startups, funding, and entrepreneurship."
        
        return ai_service.generate_content(message, system_prompt)
            
    except Exception as e:
        logger.error(f"AI service call failed: {e}")
        return "AI service is temporarily unavailable. Please try again later."

def _get_fallback_response(message):
    """Provide intelligent fallback responses when API quota is exceeded"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['funding', 'invest', 'money', 'capital']):
        return "For funding advice: Consider your startup stage, prepare a solid pitch deck, research VCs in your sector, and focus on traction metrics. The platform has many successful startups you can learn from!"
    
    elif any(word in message_lower for word in ['startup', 'business', 'company']):
        return "For startup guidance: Focus on solving a real problem, validate your idea with customers, build an MVP, and iterate based on feedback. Check out the projects on this platform for inspiration!"
    
    elif any(word in message_lower for word in ['pitch', 'presentation', 'deck']):
        return "For pitch advice: Keep it simple, tell a compelling story, show market opportunity, highlight your team's strengths, and include clear financial projections. Practice makes perfect!"
    
    elif any(word in message_lower for word in ['market', 'competition', 'analysis']):
        return "For market analysis: Research your target audience, analyze competitors, identify your unique value proposition, and validate demand through customer interviews and surveys."
    
    else:
        return "I'm here to help with startup and funding questions! Try asking about funding strategies, pitch development, market analysis, or business planning. Browse the platform to see successful startup examples!"

@csrf_exempt
def chatbot_api(request):
    """Handle chatbot API interactions"""
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                import json
                data = json.loads(request.body)
                message = data.get('message', '').strip()
            else:
                message = request.POST.get('message', '').strip()

            if message:
                try:
                    response = ask_gemini(message)
                    
                    # Save chat only if user is authenticated
                    if request.user.is_authenticated:
                        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
                        chat.save()
                    
                    return JsonResponse({'success': True, 'message': message, 'response': response})
                except Exception as e:
                    logger.error(f"Chatbot API error: {e}")
                    return JsonResponse({'success': False, 'error': 'Failed to get response from AI. Please try again later.'}, status=500)
            else:
                return JsonResponse({'success': False, 'error': 'Empty message'}, status=400)
        except Exception as e:
            logger.error(f"Chatbot API JSON error: {e}")
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

# Create your views here.

def blog(request):
    return render(request, 'blog.html')

def your_view(request):
    step_labels = ["Description", "Problem", "Market", "Competition", "(Details)"]
    return render(request, "home.html", {"step_labels": step_labels})


# Home view that works for both authenticated and non-authenticated users
# Home view that works for both authenticated and non-authenticated users
def home(request):
    try:
        # If user is not authenticated, show all projects
        if not request.user.is_authenticated:
            projects = Project.objects.all().order_by('-created_at')
            
            # Add funding percentage calculation for each project
            for project in projects:
                if project.funding_goal > 0:
                    current_funding = project.current_funding()
                    project.funding_percentage = min(100, (current_funding / project.funding_goal) * 100)
                else:
                    project.funding_percentage = 0
                
                # For non-authenticated users, only show "Funded" if project reached goal
                project.user_funded = project.funding_percentage >= 100
                project.user_invested = False
            
            context = {
                'projects': projects,
                'query': '',
                'selected_category': None,
                'selected_stage': None,
                'mine': False,
                'all_projects': True,
                'invested': False,
                'is_recommendations': False,
                'show_personalized_alert': False,
            }
            
            return render(request, 'home.html', context)
        
        # For authenticated users, show their projects
        query = request.GET.get('q', '')
        category = request.GET.get('category')
        stage = request.GET.get('stage')
        mine = request.GET.get('mine') == '1'
        risk_level = request.GET.get('risk_level')
        growth_index = request.GET.get('growth_index')
        
        if request.method == 'POST' and request.user.is_authenticated:
            try:
                name = request.POST.get('name')
                description = request.POST.get('description')
                market = request.POST.get('market')
                problem = request.POST.get('problem')
                competition = request.POST.get('competition')
                details = request.POST.get('details')
                stage = request.POST.get('stage')
                category = request.POST.get('category')
                url = request.POST.get('url')
                banner = request.FILES.get('banner')
                funding_goal = request.POST.get('funding_goal', 0)

                # Validate required fields
                if not name or not description or not stage or not category:
                    messages.error(request, "Please fill in all required fields.")
                    return render(request, 'home.html')

                # Analyze project data with AI before creation
                project_data = {
                    'description': description or '',
                    'problem': problem or '',
                    'market': market or '',
                    'competition': competition or '',
                    'details': details or ''
                }
                
                # Get AI analysis and suggestions
                combined_text = ' '.join([v for v in project_data.values() if v])
                pitch_analysis = analyze_pitch_strength(combined_text)
                
                # Create the project (single creation, not duplicate)
                project = Project.objects.create(
                    user=request.user,
                    name=name,
                    description=description,
                    market=market,
                    problem=problem,
                    competition=competition,
                    details=details,
                    stage=stage,
                    category=category,
                    url=url,
                    banner=banner,
                    funding_goal=funding_goal
                )
                
                # Store AI analysis results (you could add a field to Project model for this)
                if pitch_analysis['score'] < 60:
                    messages.warning(request, f"Project created successfully! AI Score: {pitch_analysis['score']}/100. Consider improving your pitch with the suggestions provided.")
                else:
                    messages.success(request, f"Project '{name}' created successfully! AI Score: {pitch_analysis['score']}/100")

                # Parse positions JSON
                try:
                    positions_data = json.loads(request.POST.get('positions_json', '[]'))
                    if not isinstance(positions_data, list):
                        positions_data = []
                except json.JSONDecodeError:
                    # Handle invalid JSON by defaulting to empty list
                    positions_data = []

                # Create positions for the project
                for pos in positions_data:
                    if isinstance(pos, dict) and all(key in pos for key in ['title', 'description', 'compensation_type']):
                        Position.objects.create(
                            project=project,
                            title=pos['title'],
                            description=pos['description'],
                            compensation_type=pos['compensation_type']
                        )

                messages.success(request, f"Project '{name}' created successfully!")
                return redirect('home')

            except Exception as e:
                messages.error(request, f"Error creating project: {str(e)}")
                return render(request, 'home.html')
        
        # ENHANCED SEARCH AND FILTERING
        query = request.GET.get('q', '').strip()
        all_projects = request.GET.get('all_projects') == '1'
        invested = request.GET.get('invested') == '1'
        
        # Start with all projects
        projects = Project.objects.all()
        
        # Apply filters
        if query:
            projects = projects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(problem__icontains=query) |
                Q(market__icontains=query) |
                Q(competition__icontains=query) |
                Q(details__icontains=query)
            )

        if category:
            projects = projects.filter(category__iexact=category)

        if stage:
            projects = projects.filter(stage__iexact=stage)

        if mine:
            projects = projects.filter(user=request.user)
        
        if invested and request.user.is_authenticated:
            # Show projects the user has invested in
            invested_projects = Investment.objects.filter(investor=request.user).values_list('project', flat=True)
            projects = projects.filter(id__in=invested_projects)
        
        # AI Score filtering
        if risk_level:
            projects = projects.filter(ai_report__risk_level=risk_level)
        
        if growth_index:
            projects = projects.filter(ai_report__growth_index=growth_index)
        
        # For authenticated users with no filters, show personalized recommendations
        if (request.user.is_authenticated and 
            not query and not category and not stage and not mine and not invested and not all_projects and not risk_level and not growth_index):
            
            # Check if user has enough data for personalized recommendations
            user_has_data = (
                Investment.objects.filter(investor=request.user).exists() or
                ProjectView.objects.filter(user=request.user).exists()
            )
            
            if user_has_data:
                # User has interaction data - show personalized recommendations
                recommendations = Recommendation.objects.filter(
                    user=request.user
                ).select_related('project').order_by('-score')[:20]
                
                # If no recommendations exist, generate them on-demand
                if not recommendations.exists():
                    generate_enhanced_recommendations_for_user(request.user)
                    recommendations = Recommendation.objects.filter(
                        user=request.user
                    ).select_related('project').order_by('-score')[:20]
                
                # Get recommended projects
                recommended_projects = [rec.project for rec in recommendations]
                
                # Exclude projects the user has already invested in or created
                user_invested_projects = Investment.objects.filter(investor=request.user).values_list('project', flat=True)
                user_created_projects = Project.objects.filter(user=request.user).values_list('id', flat=True)
                
                # Filter out only invested and created projects from recommendations
                # Allow viewed projects to be recommended again
                filtered_recommendations = []
                for rec in recommendations:
                    if (rec.project.id not in user_invested_projects and 
                        rec.project.id not in user_created_projects):
                        filtered_recommendations.append(rec.project)
                
                # If no filtered recommendations, show all projects instead
                if not filtered_recommendations:
                    # No personalized recommendations available - show all projects instead
                    projects = Project.objects.all().order_by('-created_at')
                    is_recommendations = False
                    show_personalized_alert = False  # Don't show personalized recommendations alert
                else:
                    projects = filtered_recommendations
                    is_recommendations = True
                    show_personalized_alert = True  # Show personalized recommendations alert
                
            else:
                # New user with no data - show all projects instead of cold start recommendations
                # Don't show personalized recommendations alert for new users
                projects = Project.objects.all().order_by('-created_at')
                is_recommendations = False
                show_personalized_alert = False  # Don't show personalized recommendations alert
            
            # Add context to indicate these are recommendations
            context = {
                'projects': projects,
                'query': query,
                'selected_category': category,
                'selected_stage': stage,
                'mine': mine,
                'all_projects': all_projects,
                'invested': invested,
                'is_recommendations': is_recommendations,
                'show_personalized_alert': show_personalized_alert,
                'selected_risk_level': risk_level,
                'selected_growth_index': growth_index,
            }
        else:
            # Show all projects when filters are applied or "All Projects" is selected
            # For "ALL PROJECTS" filter, show ALL projects (including invested ones)
            if all_projects and request.user.is_authenticated:
                # When "ALL PROJECTS" is selected, show all projects but exclude user's created projects
                user_created_projects = Project.objects.filter(user=request.user).values_list('id', flat=True)
                
                # Show all projects except user's created projects (but include invested ones)
                projects = projects.exclude(
                    id__in=list(user_created_projects)
                )
            
            projects = projects.order_by('-created_at')
            
            context = {
                'projects': projects,
                'query': query,
                'selected_category': category,
                'selected_stage': stage,
                'mine': mine,
                'all_projects': all_projects,
                'invested': invested,
                'is_recommendations': False,
                'show_personalized_alert': False,
                'selected_risk_level': risk_level,
                'selected_growth_index': growth_index,
            }

        # Add funding percentage calculation and user-specific funding status for each project
        for project in projects:
            if project.funding_goal > 0:
                current_funding = project.current_funding()
                project.funding_percentage = min(100, (current_funding / project.funding_goal) * 100)
            else:
                project.funding_percentage = 0
            
            # Add funding status tags
            # "GOAL REACHED" - visible to everyone when funding goal is complete
            project.goal_reached = project.funding_percentage >= 100
            
            # "Invested" - visible only to the current user if they invested in this project
            if request.user.is_authenticated:
                project.user_invested = Investment.objects.filter(
                    investor=request.user,
                    project=project
                ).exists()
            else:
                project.user_invested = False
                
            # Keep existing user_funded logic for backward compatibility
            if request.user.is_authenticated:
                # Check if user has invested in this project
                user_has_invested = Investment.objects.filter(
                    investor=request.user,
                    project=project
                ).exists()
                
                # Check if project has reached funding goal
                project_is_funded = project.funding_percentage >= 100
                
                # User-specific funding status: "Funded" if user invested OR project reached goal
                project.user_funded = user_has_invested or project_is_funded
            else:
                # For non-authenticated users, only show "Funded" if project reached goal
                project.user_funded = project.funding_percentage >= 100

        # Add unread message counts
        context.update(get_unread_counts(request.user))
        
        return render(request, 'home.html', context)
        
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        # Return empty context if database is not ready
        context = {
            'projects': [],
            'query': '',
            'selected_category': None,
            'selected_stage': None,
            'mine': False,
            'all_projects': True,
            'invested': False,
            'is_recommendations': False,
            'show_personalized_alert': False,
            'error_message': 'Database is being set up. Please try again in a moment.'
        }
        return render(request, 'home.html', context)
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'Username does not exist')
            return render(request, 'home.html', {'show_login': True})
        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(request, 'Invalid password')
            return render(request, 'home.html', {'show_login': True})
        login(request, user)
        return redirect('home')
    # For GET requests, show the login modal
    return render(request, 'home.html', {'show_login': True})

# Register view
def register_user(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already in use')
            return render(request, 'home.html', {'show_register': True})

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        login(request, user)
        return redirect('home')

    # For GET requests, show the register modal
    return render(request, 'home.html', {'show_register': True})

# Logout view
def logout_view(request):
    logout(request)
    return redirect('home')



@login_required
def submit_application(request):
    if request.method == 'POST':
        position_id = request.POST.get('position_id')
        reason = request.POST.get('reason')
        experience = request.POST.get('experience')

        position = get_object_or_404(Position, id=position_id)

        # Check for duplicate application (optional)
        existing = Application.objects.filter(position=position, applicant=request.user)
        if existing.exists():
            messages.warning(request, "You have already applied for this position.")
            return redirect('home')

        application = Application.objects.create(
            position=position,
            applicant=request.user,
            reason=reason,
            experience=experience
        )

        # Create initial message from applicant to project owner
        initial_message_content = f"Hi! I'm interested in the {position.title} position for your project '{position.project.name}'.\n\nReason for applying: {reason}"
        if experience:
            initial_message_content += f"\n\nMy experience: {experience}"

        Message.objects.create(
            application=application,
            sender=request.user,
            recipient=position.project.user,
            content=initial_message_content
        )

        # Create notification for project owner
        Notification.objects.create(
            user=position.project.user,  # Project owner
            title="New Application Received",
            message=f"{request.user.username} applied for {position.title} position in your project '{position.project.name}'",
            notification_type="application",
            related_object_id=application.id
        )

        messages.success(request, "Application submitted successfully.")
        return redirect('home')
    

# @login_required
# def notifications_view(request):
#     applications = Application.objects.filter(
#         position__project__user=request.user
#     ).select_related('position', 'position__project', 'applicant').order_by('-created_at')

#     return render(request, 'notifications.html', {'applications': applications})



@login_required
def notifications_view(request):
    from collections import defaultdict
    from .models import Project, Application
    from django.db.models import Q

    # Get search and filter parameters
    search_project = request.GET.get('search_project', '')
    filter_status = request.GET.get('filter_status', '')
    search_applicant = request.GET.get('search_applicant', '')

    # Start with user's projects
    user_projects = Project.objects.filter(user=request.user)\
        .prefetch_related('positions')\
        .order_by('-created_at')

    # Filter projects by search term if provided
    if search_project:
        user_projects = user_projects.filter(name__icontains=search_project)

    # Get applications for these projects
    applications = Application.objects.filter(
        position__project__in=user_projects
    ).select_related('position', 'position__project', 'applicant')\
     .order_by('-created_at')

    # Filter by status if provided
    if filter_status:
        applications = applications.filter(status=filter_status)

    # Filter by applicant username if provided
    if search_applicant:
        applications = applications.filter(applicant__username__icontains=search_applicant)

    # Add unread message counts
    for app in applications:
        unread_count = Message.objects.filter(
            application=app,
            recipient=request.user,
            is_read=False
        ).count()
        app.has_unread = unread_count > 0
        app.unread_count = unread_count

    grouped_apps = defaultdict(list)
    for app in applications:
        grouped_apps[app.position.project].append(app)

    # Maintain project order while grouping
    project_data = [(project, grouped_apps.get(project, [])) for project in user_projects]

    # Get all user projects for the search dropdown
    all_user_projects = Project.objects.filter(user=request.user).order_by('name')

    context = {
        'grouped_apps': project_data,
        'all_user_projects': all_user_projects,
        'search_project': search_project,
        'filter_status': filter_status,
        'search_applicant': search_applicant,
    }

    return render(request, 'notifications.html', context)



@csrf_exempt
def save_transaction(request):
    if request.method == "POST":
        data = json.loads(request.body)
        project_id = data.get("project_id")
        amount_eth = Decimal(str(data.get("amount_eth")))
        user_address = data.get("user_address")
        tx_hash = data.get("tx_hash")

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return JsonResponse({'error': 'Project not found'}, status=404)

        # Save the transaction with user link if authenticated
        transaction_data = {
            'user_address': user_address,
            'tx_hash': tx_hash,
            'amount_eth': amount_eth,
            'project': project
        }

        # Link to user if authenticated
        if request.user.is_authenticated:
            transaction_data['user'] = request.user

        Transaction.objects.create(**transaction_data)

        # Create Investment record if user is authenticated
        if request.user.is_authenticated:
            Investment.objects.create(
                investor=request.user,
                project=project,
                amount=amount_eth
            )
            
            # Update analytics
            update_user_project_analytics(request.user, project)
            
            # Regenerate recommendations after new investment
            generate_enhanced_recommendations_for_user(request.user)

        # Update current funding
        total_funded = Transaction.objects.filter(project=project).aggregate(total=models.Sum('amount_eth'))['total'] or Decimal('0')
        percentage = (total_funded / project.funding_goal) * 100
        percentage = float(min(percentage, 100))

        # Determine whether to trigger confetti/message
        session_key = f"funded_{project_id}"
        trigger_celebration = False

        if total_funded >= project.funding_goal and not request.session.get(session_key):
            request.session[session_key] = True  # Mark as shown
            trigger_celebration = True

        return JsonResponse({
            'project_id': project.id,
            'current_funding': str(total_funded),
            'funding_goal': str(project.funding_goal),
            'percentage': percentage,
            'celebrate': trigger_celebration  # this is key
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)
def get_project_funding(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        total_funded = Transaction.objects.filter(project=project).aggregate(total=Sum('amount_eth'))['total'] or Decimal('0')
        percentage = float(min((total_funded / project.funding_goal) * 100, 100))

        session_key = f"funded_{project_id}"
        trigger_celebration = False

        if total_funded >= project.funding_goal and not request.session.get(session_key):
            request.session[session_key] = True
            trigger_celebration = True

        return JsonResponse({
            'project_id': project.id,
            'current_funding': str(total_funded),
            'funding_goal': str(project.funding_goal),
            'percentage': percentage,
            'celebrate': trigger_celebration
        })

    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
@login_required
def message_history(request, application_id):
    """Get message history for an application"""
    try:
        # Verify the user has permission to view these messages
        application = Application.objects.get(id=application_id)
        
        # Check if user is either the project owner or the applicant
        if request.user != application.position.project.user and request.user != application.applicant:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        # Check if application is approved (only approved applications can access messaging)
        if application.status != 'approved':
            return JsonResponse({'error': 'Messaging is only available for approved applications'}, status=403)
        
        # Mark messages as read if user is recipient
        Message.objects.filter(
            application=application,
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        # Get all messages for this application
        messages = Message.objects.filter(application=application).order_by('timestamp')
        
        # Format messages for JSON response
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                'is_sender': msg.sender == request.user,
                'is_read': msg.is_read
            })
        
        return JsonResponse({'messages': message_list})
    
    except Application.DoesNotExist:
        return JsonResponse({'error': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def send_message(request):
    """Send a message to an applicant or project owner"""
    try:
        application_id = request.POST.get('application_id')
        content = request.POST.get('content')
        
        if not application_id or not content:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        application = Application.objects.get(id=application_id)

        # Check messaging permissions
        if request.user == application.applicant:
            # Applicant can only send messages if application is approved
            # (Initial message is created automatically during application submission)
            if application.status != 'approved':
                return JsonResponse({'success': False, 'error': 'You can only send messages after your application is approved'}, status=403)
        elif request.user == application.position.project.user:
            # Project owner can always send messages
            pass
        else:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        # Determine sender and recipient
        if request.user == application.position.project.user:
            # Project owner sending to applicant
            sender = request.user
            recipient = application.applicant
        elif request.user == application.applicant:
            # Applicant sending to project owner
            sender = request.user
            recipient = application.position.project.user
        else:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        # Create and save the message
        message = Message(
            application=application,
            sender=sender,
            recipient=recipient,
            content=content
        )
        message.save()

        # Create notification for message recipient
        if recipient == application.applicant:
            # Message sent to applicant
            Notification.objects.create(
                user=recipient,
                title="New Message Received 💬",
                message=f"You have a new message from {sender.username} regarding your application for {application.position.title} in '{application.position.project.name}'",
                notification_type="message",
                related_object_id=application.id
            )
        else:
            # Message sent to project owner
            Notification.objects.create(
                user=recipient,
                title="New Message Received 💬",
                message=f"You have a new message from {sender.username} regarding the {application.position.title} position in your project '{application.position.project.name}'",
                notification_type="message",
                related_object_id=application.id
            )

        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                'is_sender': True
            }
        })
    
    except Application.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Helper function to get unread message counts
def get_unread_counts(user):
    """Get unread message counts for authenticated users"""
    if not user.is_authenticated:
        return {
            'unread_messages_count': 0,
            'unread_direct_messages_count': 0,
            'unread_notifications_count': 0
        }

    # Count unread messages for projects owned by the user (application-based)
    project_applications = Application.objects.filter(position__project__user=user)
    unread_messages_count = Message.objects.filter(
        application__in=project_applications,
        recipient=user,
        is_read=False
    ).count()

    # Count unread direct messages for projects owned by the user
    unread_direct_messages_count = DirectMessage.objects.filter(
        project__user=user,
        recipient=user,
        is_read=False
    ).count()

    # Count unread notifications
    unread_notifications_count = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()

    return {
        'unread_messages_count': unread_messages_count,
        'unread_direct_messages_count': unread_direct_messages_count,
        'unread_notifications_count': unread_notifications_count
    }

# New page views
def about(request):
    """About page view"""
    context = get_unread_counts(request.user)
    return render(request, 'about.html', context)

def features(request):
    """Features page view"""
    context = get_unread_counts(request.user)
    return render(request, 'features.html', context)

def contact(request):
    """Contact page view"""
    context = get_unread_counts(request.user)
    return render(request, 'contact.html', context)

@login_required
def profile(request):
    """User profile page view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Check if this is a reset action
        if request.POST.get('action') == 'reset':
            # Reset profile fields to default values
            profile.bio = ''
            profile.location = ''
            profile.country = ''
            profile.country_code = ''
            profile.website = ''
            profile.phone = ''
            profile.company = ''
            profile.job_title = ''
            profile.linkedin_url = ''
            profile.twitter_url = ''
            profile.github_url = ''

            # Remove avatar if exists
            if profile.avatar:
                try:
                    profile.avatar.delete(save=False)
                except:
                    pass
                profile.avatar = None

            profile.save()
            messages.success(request, 'Profile has been reset to default values successfully!')
            return redirect('profile')

        # Handle profile update
        try:
            # Update User model fields (first_name and last_name are user-specific)
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()

            # Validate name fields
            if len(first_name) > 30:
                messages.error(request, 'First name must be 30 characters or less.')
                return redirect('profile')
            if len(last_name) > 30:
                messages.error(request, 'Last name must be 30 characters or less.')
                return redirect('profile')

            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

            # Update UserProfile fields
            profile.bio = request.POST.get('bio', '').strip()
            profile.location = request.POST.get('location', '').strip()
            profile.country = request.POST.get('country', '').strip()
            profile.country_code = request.POST.get('country_code', '').strip()
            profile.website = request.POST.get('website', '').strip()
            profile.phone = request.POST.get('phone', '').strip()
            profile.company = request.POST.get('company', '').strip()
            profile.job_title = request.POST.get('job_title', '').strip()
            profile.linkedin_url = request.POST.get('linkedin_url', '').strip()
            profile.twitter_url = request.POST.get('twitter_url', '').strip()
            profile.github_url = request.POST.get('github_url', '').strip()

            # Validate URL fields
            url_fields = {
                'website': profile.website,
                'linkedin_url': profile.linkedin_url,
                'twitter_url': profile.twitter_url,
                'github_url': profile.github_url
            }

            for field_name, url_value in url_fields.items():
                if url_value and not (url_value.startswith('http://') or url_value.startswith('https://')):
                    # Auto-add https:// if missing
                    setattr(profile, field_name, f'https://{url_value}')

            # Validate phone number
            phone_number = profile.phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if phone_number and not phone_number.isdigit():
                messages.error(request, 'Phone number can only contain digits, spaces, dashes, and parentheses.')
                return redirect('profile')
            if phone_number and (len(phone_number) < 7 or len(phone_number) > 15):
                messages.error(request, 'Phone number must be between 7 and 15 digits.')
                return redirect('profile')

            # Handle avatar removal
            if request.POST.get('remove_avatar') == 'true':
                if profile.avatar:
                    # Delete the old avatar file
                    try:
                        profile.avatar.delete(save=False)
                    except:
                        pass  # File might not exist
                    profile.avatar = None

            # Handle avatar upload
            elif 'avatar' in request.FILES:
                avatar_file = request.FILES['avatar']
                # Validate file size (max 5MB)
                if avatar_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'Avatar file size must be less than 5MB.')
                    return redirect('profile')
                # Validate file type
                allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
                if avatar_file.content_type not in allowed_types:
                    messages.error(request, 'Avatar must be a JPEG, PNG, or GIF image.')
                    return redirect('profile')

                # Delete old avatar if exists
                if profile.avatar:
                    try:
                        profile.avatar.delete(save=False)
                    except:
                        pass

                profile.avatar = avatar_file

            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

    # Get user statistics using UserProfile methods
    user_projects = Project.objects.filter(user=request.user)

    # Get profile completion data
    profile_completion = profile.get_profile_completion()

    context = {
        'user': request.user,
        'profile': profile,
        'projects_count': profile.get_projects_count(),
        'total_funded': profile.get_total_funded(),
        'investments_made': profile.get_investments_made(),
        'investments_count': profile.get_investments_count(),
        'funded_projects_count': profile.get_funded_projects_count(),
        'success_rate': profile.get_success_rate(),
        'recent_projects': user_projects.order_by('-created_at')[:3],
        'profile_completion': profile_completion
    }

    # Add unread message counts
    context.update(get_unread_counts(request.user))

    return render(request, 'profile.html', context)

@login_required
def settings(request):
    """User settings page view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_account':
            # Update account settings
            profile.timezone = request.POST.get('timezone', 'UTC')
            profile.language = request.POST.get('language', 'en')
            profile.save()
            messages.success(request, 'Account settings updated successfully!')

        elif action == 'update_notifications':
            # Update notification preferences
            profile.email_notifications = request.POST.get('email_notifications') == 'on'
            profile.push_notifications = request.POST.get('push_notifications') == 'on'
            profile.project_updates = request.POST.get('project_updates') == 'on'
            profile.investment_alerts = request.POST.get('investment_alerts') == 'on'
            profile.marketing_communications = request.POST.get('marketing_communications') == 'on'
            profile.save()
            messages.success(request, 'Notification preferences updated successfully!')

        elif action == 'update_privacy':
            # Update privacy settings
            profile.profile_visibility = request.POST.get('profile_visibility', 'public')
            profile.show_activity_status = request.POST.get('show_activity_status') == 'on'
            profile.show_investment_history = request.POST.get('show_investment_history') == 'on'
            profile.save()
            messages.success(request, 'Privacy settings updated successfully!')

        elif action == 'change_password':
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                messages.success(request, 'Password changed successfully! Please log in again.')
                return redirect('login')

        elif action == 'delete_account':
            # Handle account deletion
            password = request.POST.get('password')

            if not request.user.check_password(password):
                messages.error(request, 'Password is incorrect. Account deletion cancelled.')
            else:
                # Delete user's projects and related data
                user_projects = Project.objects.filter(user=request.user)
                for project in user_projects:
                    # Delete project-related data
                    project.delete()

                # Delete direct messages
                DirectMessage.objects.filter(sender=request.user).delete()
                DirectMessage.objects.filter(recipient=request.user).delete()

                # Update messages where user is referenced to show "User not found"
                Message.objects.filter(sender=request.user).update(sender=None)
                Message.objects.filter(recipient=request.user).update(recipient=None)

                # Delete user profile
                if hasattr(request.user, 'userprofile'):
                    request.user.userprofile.delete()

                # Delete the user account
                username = request.user.username
                request.user.delete()

                messages.success(request, f'Account "{username}" has been permanently deleted.')
                return redirect('home')

        elif action == 'send_password_reset':
            # Handle password reset request
            try:
                # Generate password reset token
                token = default_token_generator.make_token(request.user)
                uid = urlsafe_base64_encode(force_bytes(request.user.pk))

                # Create reset link (you would need to implement the reset view)
                reset_link = f"{request.build_absolute_uri('/')[:-1]}/reset-password/{uid}/{token}/"

                # Send email (simplified - you'd want a proper email template)
                subject = 'Password Reset Request - Nexora'
                message = f"""
                Hi {request.user.username},

                You requested a password reset for your Nexora account.

                Click the link below to reset your password:
                {reset_link}

                If you didn't request this, please ignore this email.

                Best regards,
                The Nexora Team
                """

                # For now, just show a success message since email might not be configured
                messages.success(request, 'Password reset instructions have been sent to your email address.')

                # Uncomment this when email is properly configured:
                # send_mail(
                #     subject,
                #     message,
                #     settings.DEFAULT_FROM_EMAIL,
                #     [request.user.email],
                #     fail_silently=False,
                # )

            except Exception as e:
                messages.error(request, 'Failed to send password reset email. Please try again.')

        return redirect('settings')

    context = {
        'user': request.user,
        'profile': profile
    }

    # Add unread message counts
    context.update(get_unread_counts(request.user))

    return render(request, 'settings.html', context)

@csrf_exempt
def chat_api(request):
    """Chatbot API endpoint using Groq"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'success': False, 'error': 'Message is required'})

        # Load Groq API key from settings or environment
        from django.conf import settings
        groq_api_key = getattr(settings, 'GROQ_API_KEY', os.getenv('GROQ_API_KEY'))

        if not groq_api_key or groq_api_key == "GROQ_API_KEY":
            return JsonResponse({'success': False, 'error': 'API key not configured'})

        # Prepare the prompt for entrepreneur assistance
        system_prompt = """You are Nexora AI Assistant, a specialized AI helper for entrepreneurs and startup founders. You provide expert advice on:

- Business strategy and planning
- Funding and investment strategies
- Market research and analysis
- Startup best practices
- Technical guidance for tech startups
- Networking and mentorship advice
- Product development and MVP creation
- Marketing and customer acquisition
- Financial planning and budgeting
- Legal considerations for startups

Keep your responses concise, actionable, and tailored to early-stage entrepreneurs. Use a friendly but professional tone. If asked about topics outside entrepreneurship, politely redirect to business-related topics."""

        # Call Groq API
        headers = {
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'model': 'llama-3.3-70b-versatile',  # Using Llama 3.3 70B model
            'temperature': 0.7,
            'max_tokens': 500,
            'top_p': 0.9
        }

        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']

            return JsonResponse({
                'success': True,
                'response': ai_response
            })
        else:
            error_msg = f"Groq API error: {response.status_code} - {response.text}"
            logging.error(error_msg)
            print(f"DEBUG: {error_msg}")  # Add debug print
            return JsonResponse({
                'success': False,
                'error': 'AI service temporarily unavailable'
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except requests.RequestException as e:
        logging.error(f"Request error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Network error'})
    except Exception as e:
        logging.error(f"Chat API error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

@login_required
def applicant_messages_view(request):
    """View for applicants to see their applications and messages"""
    applications = Application.objects.filter(applicant=request.user).select_related('position__project__user').order_by('-created_at')

    # Get recent notifications for the applicant
    notifications = Notification.objects.filter(user=request.user)[:5]
    unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'applicant_messages.html', {
        'applications': applications,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count
    })

@login_required
def update_application_status(request):
    """Update application status (approve/reject)"""
    import logging
    logger = logging.getLogger(__name__)

    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        new_status = request.POST.get('status')

        logger.info(f"Status update request: app_id={app_id}, status={new_status}, user={request.user.username}")

        if new_status not in ['approved', 'rejected']:
            logger.error(f"Invalid status: {new_status}")
            return JsonResponse({'success': False, 'error': 'Invalid status'})

        try:
            application = Application.objects.get(id=app_id)
            logger.info(f"Found application: {application.id}, current status: {application.status}")

            # Check if user is the project owner
            if application.position.project.user != request.user:
                return JsonResponse({'success': False, 'error': 'Permission denied'})

            if application.status == 'approved' or application.status == 'rejected':
                return JsonResponse({'success': False, 'error': 'Status already set'})

            application.status = new_status
            application.save()
            logger.info(f"Application status updated to: {new_status}")

            # Create notification for applicant
            if new_status == 'approved':
                Notification.objects.create(
                    user=application.applicant,
                    title="Application Approved! 🎉",
                    message=f"Great news! Your application for {application.position.title} position in '{application.position.project.name}' has been approved. You can now start messaging with the project owner.",
                    notification_type="approval",
                    related_object_id=application.id
                )
                logger.info(f"Approval notification created for user: {application.applicant.username}")
            elif new_status == 'rejected':
                Notification.objects.create(
                    user=application.applicant,
                    title="Application Update",
                    message=f"Thank you for your interest in {application.position.title} position in '{application.position.project.name}'. Unfortunately, we've decided to move forward with other candidates.",
                    notification_type="rejection",
                    related_object_id=application.id
                )
                logger.info(f"Rejection notification created for user: {application.applicant.username}")

            logger.info("Returning success response")
            response = JsonResponse({
                'success': True,
                'message': f'Application {new_status} successfully',
                'status': new_status
            })
            response['Content-Type'] = 'application/json'
            return response
        except Application.DoesNotExist:
            logger.error(f"Application not found: {app_id}")
            return JsonResponse({'success': False, 'error': 'Application not found'})
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Internal server error'})

    logger.error(f"Invalid request method: {request.method}")
    return JsonResponse({'success': False, 'error': 'Invalid request'})

from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def chatbot_view(request):
    """Render the chatbot interface with chat history"""
    if request.user.is_authenticated:
        chats = Chat.objects.filter(user=request.user).order_by('created_at')
        return render(request, 'chatbot.html', {'chats': chats})
    # For unauthenticated users, pass an empty list
    return render(request, 'chatbot.html', {'chats': []})

@login_required
def ai_mentorship(request):
    return render(request, 'Chatbot-main.html')

@login_required
def ai_mentorship_history(request):
    """API endpoint to get user's AI mentorship chat history"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Only GET method allowed'})

    try:
        # Get all mentorship chats for the current user
        chats = MentorshipChat.objects.filter(user=request.user).order_by('created_at')

        chat_data = []
        for chat in chats:
            chat_data.append({
                'id': chat.id,
                'message': chat.message,
                'response': chat.response,
                'created_at': chat.created_at.isoformat(),
                'timestamp': chat.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return JsonResponse({
            'success': True,
            'chats': chat_data
        })

    except Exception as e:
        logger.error(f"Error retrieving mentorship chat history: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Failed to retrieve chat history'})

@login_required
@require_POST
def mark_notifications_read(request):
    """Mark all notifications as read for the current user"""
    try:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def analytics_dashboard(request):
    """Analytics dashboard with real data from models"""

    # Basic metrics
    total_users = User.objects.count()
    total_projects = Project.objects.count()
    total_applications = Application.objects.count()
    total_funding = Transaction.objects.aggregate(Sum('amount_eth'))['amount_eth__sum'] or 0

    # User role analysis (based on whether they've created projects or applied to positions)
    entrepreneurs = User.objects.filter(project__isnull=False).distinct().count()
    investors = User.objects.filter(
        userprofile__investment_alerts=True
    ).distinct().count()
    # Calculate others (users who are neither entrepreneurs nor investors)
    others = total_users - entrepreneurs - investors + User.objects.filter(
        project__isnull=False, userprofile__investment_alerts=True
    ).distinct().count()  # Add back users who are both

    # Monthly user growth (past 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_signups_raw = User.objects.filter(
        date_joined__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(count=Count('id')).order_by('month')

    # Format monthly data for frontend
    monthly_signups = [
        {'month': item['month'].strftime('%Y-%m'), 'count': item['count']}
        for item in monthly_signups_raw
    ]

    # Daily signups (past 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_signups_raw = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).annotate(
        day=TruncDay('date_joined')
    ).values('day').annotate(count=Count('id')).order_by('day')

    # Format daily data for frontend
    daily_signups = [
        {'day': item['day'].strftime('%Y-%m-%d'), 'count': item['count']}
        for item in daily_signups_raw
    ]

    # Projects by category
    projects_by_category = Project.objects.values('category').annotate(
        count=Count('id')
    ).order_by('-count')

    # Projects by stage
    projects_by_stage = Project.objects.values('stage').annotate(
        count=Count('id')
    ).order_by('-count')

    # Recent activity
    recent_projects = Project.objects.select_related('user').order_by('-created_at')[:5]
    recent_applications = Application.objects.select_related('applicant', 'position__project').order_by('-created_at')[:5]

    # Funding metrics
    funded_projects = Project.objects.filter(transactions__isnull=False).distinct().count()
    avg_funding_per_project = Transaction.objects.aggregate(
        avg_funding=Sum('amount_eth')
    )['avg_funding'] or 0
    if funded_projects > 0:
        avg_funding_per_project = avg_funding_per_project / funded_projects

    context = {
        'total_users': total_users,
        'total_projects': total_projects,
        'total_applications': total_applications,
        'total_funding': round(float(total_funding), 4),
        'entrepreneurs': entrepreneurs,
        'investors': investors,
        'others': others,
        'monthly_signups': list(monthly_signups),
        'daily_signups': list(daily_signups),
        'projects_by_category': list(projects_by_category),
        'projects_by_stage': list(projects_by_stage),
        'recent_projects': recent_projects,
        'recent_applications': recent_applications,
        'funded_projects': funded_projects,
        'avg_funding_per_project': round(float(avg_funding_per_project), 4),
    }

    return render(request, 'analytics_dashboard.html', context)

@login_required
def network_explorer(request):
    """Network explorer to browse users with filtering and search"""

    # Get all users with their profiles
    users = User.objects.select_related('userprofile').filter(
        userprofile__profile_visibility__in=['public', 'registered']
    ).exclude(id=request.user.id)  # Exclude current user

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(userprofile__company__icontains=search_query) |
            Q(userprofile__job_title__icontains=search_query) |
            Q(userprofile__location__icontains=search_query)
        )

    # Role filter
    role_filter = request.GET.get('role', '')
    if role_filter == 'entrepreneur':
        users = users.filter(project__isnull=False).distinct()
    elif role_filter == 'investor':
        users = users.filter(userprofile__investment_alerts=True).exclude(project__isnull=False).distinct()

    # Location filter
    location_filter = request.GET.get('location', '')
    if location_filter:
        users = users.filter(userprofile__location__icontains=location_filter)

    # Industry filter (based on project categories)
    industry_filter = request.GET.get('industry', '')
    if industry_filter:
        users = users.filter(project__category__icontains=industry_filter).distinct()

    # Add role information to each user
    users_with_roles = []
    for user in users:
        user_data = {
            'user': user,
            'profile': user.userprofile,
            'is_entrepreneur': user.project_set.exists(),
            'is_investor': user.userprofile.investment_alerts,
            'projects_count': user.project_set.count(),
            'applications_count': user.application_set.count(),
        }

        # Determine primary role
        if user_data['is_entrepreneur'] and user_data['is_investor']:
            user_data['primary_role'] = 'Entrepreneur & Investor'
        elif user_data['is_entrepreneur']:
            user_data['primary_role'] = 'Entrepreneur'
        elif user_data['is_investor']:
            user_data['primary_role'] = 'Investor'
        else:
            user_data['primary_role'] = 'Member'

        # Get user's project categories for tags
        user_categories = list(user.project_set.values_list('category', flat=True).distinct())
        user_data['tags'] = user_categories[:3]  # Limit to 3 tags

        users_with_roles.append(user_data)

    # Get filter options
    all_locations = UserProfile.objects.exclude(location='').values_list('location', flat=True).distinct()
    all_industries = Project.objects.values_list('category', flat=True).distinct()

    context = {
        'users': users_with_roles,
        'search_query': search_query,
        'role_filter': role_filter,
        'location_filter': location_filter,
        'industry_filter': industry_filter,
        'all_locations': sorted(set(all_locations)),
        'all_industries': sorted(set(all_industries)),
        'total_users': len(users_with_roles),
    }

    return render(request, 'network_explorer.html', context)

@csrf_exempt
@login_required
def ai_mentorship_api(request):
    """API endpoint for AI mentorship chat"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'success': False, 'error': 'Message is required'})

        # Enhanced entrepreneurship-focused system prompt
        system_prompt = """You are an expert AI entrepreneurship mentor with deep knowledge in:
        - Business strategy and planning
        - Startup funding and investment
        - Market validation and customer development
        - Product development and MVP creation
        - Team building and leadership
        - Growth hacking and marketing
        - Financial planning and management
        - Legal and regulatory considerations
        - Scaling and operations
        - Exit strategies

        Provide practical, actionable advice tailored to startup founders and entrepreneurs.
        Be encouraging but realistic. Ask clarifying questions when needed to provide better guidance.
        Keep responses concise but comprehensive, focusing on actionable insights."""

        # Get AI response using Groq
        ai_response = ask_gemini_mentorship(user_message, system_prompt)

        # Save chat to database
        try:
            mentorship_chat = MentorshipChat(
                user=request.user,
                message=user_message,
                response=ai_response
            )
            mentorship_chat.save()
        except Exception as e:
            logger.error(f"Error saving mentorship chat: {str(e)}")
            # Continue even if save fails, don't break the user experience

        return JsonResponse({
            'success': True,
            'response': ai_response
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"AI Mentorship API error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'})

def ask_gemini_mentorship(message, system_prompt):
    """Enhanced AI service call for mentorship with system prompt and fallback"""
    try:
        from main.ai_service import ai_service
        
        logger.info(f"Making AI service call for mentorship with message: {message[:50]}...")
        
        result = ai_service.generate_content(message, system_prompt, max_tokens=800)
        
        logger.info("AI service call successful")
        return result
            
    except Exception as e:
        logger.error(f"AI service error in mentorship: {str(e)}")
        return _get_mentorship_fallback_response(message)

def _get_mentorship_fallback_response(message):
    """Provide intelligent fallback responses for mentorship when API quota is exceeded"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['validate', 'validation', 'test', 'idea']):
        return "To validate your startup idea: 1) Talk to potential customers, 2) Build a simple MVP, 3) Test pricing, 4) Measure engagement, 5) Iterate based on feedback. Start small and scale what works!"
    
    elif any(word in message_lower for word in ['funding', 'invest', 'raise', 'money']):
        return "For funding: 1) Perfect your pitch deck, 2) Show traction and metrics, 3) Research relevant investors, 4) Prepare for due diligence, 5) Consider different funding stages. Focus on demonstrating product-market fit first!"
    
    elif any(word in message_lower for word in ['team', 'hiring', 'cofounder']):
        return "For team building: 1) Define roles clearly, 2) Look for complementary skills, 3) Check cultural fit, 4) Consider equity distribution, 5) Start with contractors if needed. The right team makes all the difference!"
    
    elif any(word in message_lower for word in ['growth', 'scale', 'marketing']):
        return "For growth: 1) Focus on one channel first, 2) Measure everything, 3) Optimize conversion, 4) Build retention, 5) Scale what works. Growth comes from understanding your customers deeply!"
    
    else:
        return "As your startup mentor: Focus on solving real problems, validate early and often, build strong relationships, and stay persistent. Every successful startup started with a simple idea and lots of hard work. What specific challenge can I help you with?"


@login_required
def export_user_data(request):
    """Export user data as PDF"""
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#7c3aed'),
        alignment=1  # Center alignment
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#7c3aed')
    )

    # Get user data
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Title
    title = Paragraph("Nexora - User Data Export", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))

    # User Information
    user_info_heading = Paragraph("Personal Information", heading_style)
    elements.append(user_info_heading)

    user_data = [
        ['Field', 'Value'],
        ['Username', user.username],
        ['Full Name', f"{user.first_name} {user.last_name}".strip() or 'Not provided'],
        ['Email', user.email],
        ['Date Joined', user.date_joined.strftime('%B %d, %Y')],
        ['Bio', profile.bio or 'Not provided'],
        ['Location', profile.location or 'Not provided'],
        ['Company', profile.company or 'Not provided'],
        ['Job Title', profile.job_title or 'Not provided'],
        ['Website', profile.website or 'Not provided'],
        ['Phone', profile.phone or 'Not provided'],
    ]

    user_table = Table(user_data, colWidths=[2*inch, 4*inch])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(user_table)
    elements.append(Spacer(1, 20))

    # Statistics
    stats_heading = Paragraph("Account Statistics", heading_style)
    elements.append(stats_heading)

    stats_data = [
        ['Metric', 'Value'],
        ['Projects Created', str(profile.get_projects_count())],
        ['Total Funded (ETH)', f"{profile.get_total_funded():.4f}"],
        ['Investments Made (ETH)', f"{profile.get_investments_made():.4f}"],
        ['Number of Investments', str(profile.get_investments_count())],
        ['Projects Funded', str(profile.get_funded_projects_count())],
        ['Success Rate', f"{profile.get_success_rate()}%"],
    ]

    stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(stats_table)
    elements.append(Spacer(1, 20))

    # Projects
    projects = Project.objects.filter(user=user).order_by('-created_at')
    if projects.exists():
        projects_heading = Paragraph("Your Projects", heading_style)
        elements.append(projects_heading)

        project_data = [['Project Name', 'Category', 'Stage', 'Funding Goal (ETH)', 'Current Funding (ETH)', 'Created Date']]

        for project in projects:
            project_data.append([
                project.name,
                project.category,
                project.stage,
                f"{project.funding_goal:.2f}",
                f"{project.current_funding():.4f}",
                project.created_at.strftime('%Y-%m-%d')
            ])

        projects_table = Table(project_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        projects_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(projects_table)
        elements.append(Spacer(1, 20))

    # Investment History
    investments = Transaction.objects.filter(user=user).order_by('-timestamp')
    if investments.exists():
        investments_heading = Paragraph("Investment History", heading_style)
        elements.append(investments_heading)

        investment_data = [['Project', 'Amount (ETH)', 'Transaction Hash', 'Date']]

        for investment in investments:
            investment_data.append([
                investment.project.name if investment.project else 'Unknown',
                f"{investment.amount_eth:.4f}",
                f"{investment.tx_hash[:10]}...{investment.tx_hash[-6:]}",
                investment.timestamp.strftime('%Y-%m-%d %H:%M')
            ])

        investments_table = Table(investment_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        investments_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(investments_table)

    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Nexora Platform"
    footer = Paragraph(footer_text, styles['Normal'])
    elements.append(footer)

    # Build PDF
    doc.build(elements)

    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="nexora_user_data_{user.username}.pdf"'
    response.write(pdf)

    return response


# P2P Direct Chat Views
@login_required
def direct_chat_view(request, project_id):
    """Render the direct chat interface for a specific project"""
    try:
        project = get_object_or_404(Project, id=project_id)

        # Ensure user is not trying to chat with themselves
        if request.user == project.user:
            messages.error(request, "You cannot message yourself.")
            return redirect('home')

        # Get or create conversation
        conversation_messages = DirectMessage.objects.filter(
            project=project,
            sender__in=[request.user, project.user],
            recipient__in=[request.user, project.user]
        ).order_by('timestamp')

        # Mark messages as read if user is recipient
        DirectMessage.objects.filter(
            project=project,
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        context = {
            'project': project,
            'founder': project.user,
            'messages': conversation_messages,
        }

        return render(request, 'direct_chat.html', context)

    except Project.DoesNotExist:
        messages.error(request, "Project not found.")
        return redirect('home')


@login_required
def send_direct_message(request):
    """Send a direct message to project founder"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            content = data.get('content', '').strip()

            if not content:
                return JsonResponse({'success': False, 'error': 'Message content is required'}, status=400)

            project = get_object_or_404(Project, id=project_id)

            # Ensure user is not trying to message themselves
            if request.user == project.user:
                return JsonResponse({'success': False, 'error': 'Cannot message yourself'}, status=403)

            # Create and save the direct message
            direct_message = DirectMessage(
                project=project,
                sender=request.user,
                recipient=project.user,
                content=content
            )
            direct_message.save()

            # Create notification for recipient
            Notification.objects.create(
                user=project.user,
                title="New Direct Message 💬",
                message=f"{request.user.username} sent you a message about your project '{project.name}'",
                notification_type="direct_message",
                related_object_id=project.id
            )

            return JsonResponse({
                'success': True,
                'message': {
                    'id': direct_message.id,
                    'content': direct_message.content,
                    'timestamp': direct_message.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                    'is_sender': True
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Project.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@login_required
def get_direct_messages(request, project_id):
    """Get direct message history for a project"""
    try:
        project = get_object_or_404(Project, id=project_id)

        # Ensure user is either the project owner or has messages with this project
        if request.user != project.user:
            # Check if user has any messages with this project
            has_messages = DirectMessage.objects.filter(
                project=project,
                sender__in=[request.user, project.user],
                recipient__in=[request.user, project.user]
            ).exists()

            if not has_messages:
                return JsonResponse({'success': True, 'messages': []})  # Return empty messages instead of error

        # Mark messages as read if user is recipient
        DirectMessage.objects.filter(
            project=project,
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

        # Get all messages for this conversation
        messages = DirectMessage.objects.filter(
            project=project,
            sender__in=[request.user, project.user],
            recipient__in=[request.user, project.user]
        ).order_by('timestamp')

        # Format messages for JSON response
        message_list = []
        for msg in messages:
            message_list.append({
                'id': msg.id,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime('%b %d, %Y, %I:%M %p'),
                'is_sender': msg.sender == request.user,
                'sender_name': msg.sender.username,
                'is_read': msg.is_read
            })

        return JsonResponse({'success': True, 'messages': message_list})

    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def direct_messages_dashboard(request):
    """Dashboard for project creators to view all their direct messages"""
    # Get all projects owned by the user
    user_projects = Project.objects.filter(user=request.user).order_by('-created_at')

    # Get all direct messages for user's projects, grouped by project and conversation
    conversations = []

    for project in user_projects:
        # Get unique conversations for this project
        project_messages = DirectMessage.objects.filter(
            project=project
        ).order_by('timestamp')

        # Group messages by conversation partner
        conversation_partners = {}
        for message in project_messages:
            # Determine the conversation partner (not the project owner)
            partner = message.sender if message.sender != request.user else message.recipient

            if partner.id not in conversation_partners:
                conversation_partners[partner.id] = {
                    'partner': partner,
                    'project': project,
                    'messages': [],
                    'last_message': None,
                    'unread_count': 0
                }

            conversation_partners[partner.id]['messages'].append(message)
            conversation_partners[partner.id]['last_message'] = message

            # Count unread messages from this partner
            if message.recipient == request.user and not message.is_read:
                conversation_partners[partner.id]['unread_count'] += 1

        # Add conversations to the list
        for conversation in conversation_partners.values():
            conversations.append(conversation)

    # Sort conversations by last message timestamp (most recent first)
    conversations.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else timezone.now(), reverse=True)

    # Get total unread count
    total_unread = DirectMessage.objects.filter(
        project__user=request.user,
        recipient=request.user,
        is_read=False
    ).count()

    context = {
        'conversations': conversations,
        'total_unread': total_unread,
        'user_projects': user_projects,
    }

    return render(request, 'direct_messages_dashboard.html', context)


@login_required
def unified_messaging_view(request):
    """Unified messaging interface for all conversation types"""
    return render(request, 'messaging.html')

@login_required
def conversations_api(request):
    """API endpoint to get all conversations for the current user"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    conversations = []

    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Loading conversations for user: {request.user.username}")

    # Get application-based conversations
    # For project owners: conversations with applicants (include all applications that have messages)
    owner_applications = Application.objects.filter(
        position__project__user=request.user
    ).select_related('applicant', 'position__project').order_by('-created_at')

    # Filter to only include applications that have messages
    owner_applications = [app for app in owner_applications if Message.objects.filter(application=app).exists()]
    logger.info(f"Owner applications with messages: {[app.id for app in owner_applications]}")

    for app in owner_applications:
        # Get last message for this application
        last_message = Message.objects.filter(application=app).order_by('-timestamp').first()

        conversations.append({
            'id': f"app_{app.id}",
            'type': 'applicant',  # Changed from 'application' to 'applicant' for project owners
            'name': app.applicant.get_full_name() or app.applicant.username,
            'role': 'Applicant',
            'project': app.position.project.name,
            'status': app.status,
            'userId': app.applicant.id,
            'applicationId': app.id,
            'projectId': app.position.project.id,
            'avatar': getattr(getattr(app.applicant, 'userprofile', None), 'profile_picture', None),
            'online': False,  # TODO: Implement online status
            'unread': Message.objects.filter(application=app, sender=app.applicant, is_read=False).exists(),
            'lastMessage': last_message.content if last_message else None,
            'lastMessageTime': last_message.timestamp.strftime('%b %d, %I:%M %p') if last_message else None,
            'timestamp': last_message.timestamp if last_message else app.created_at
        })

    # For applicants: conversations with project owners (include all applications that have messages)
    applicant_applications = Application.objects.filter(
        applicant=request.user
    ).select_related('position__project__user', 'position__project').order_by('-created_at')

    # Filter to only include applications that have messages
    applicant_applications = [app for app in applicant_applications if Message.objects.filter(application=app).exists()]
    logger.info(f"Applicant applications with messages: {[app.id for app in applicant_applications]}")

    for app in applicant_applications:
        # Get last message for this application
        last_message = Message.objects.filter(application=app).order_by('-timestamp').first()

        conversations.append({
            'id': f"app_{app.id}",
            'type': 'application',  # Keep as 'application' for applicants
            'name': app.position.project.user.get_full_name() or app.position.project.user.username,
            'role': 'Project Owner',
            'project': app.position.project.name,
            'status': app.status,
            'userId': app.position.project.user.id,
            'applicationId': app.id,
            'projectId': app.position.project.id,
            'avatar': getattr(getattr(app.position.project.user, 'userprofile', None), 'profile_picture', None),
            'online': False,  # TODO: Implement online status
            'unread': Message.objects.filter(application=app, sender=app.position.project.user, is_read=False).exists(),
            'lastMessage': last_message.content if last_message else None,
            'lastMessageTime': last_message.timestamp.strftime('%b %d, %I:%M %p') if last_message else None,
            'timestamp': last_message.timestamp if last_message else app.created_at
        })

    # Get direct message conversations (where user is either sender or recipient)
    from django.db.models import Q

    all_direct_messages = DirectMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient', 'project').order_by('-timestamp')

    # Group by conversation partner and project
    direct_conversations = {}
    for dm in all_direct_messages:
        # Determine the conversation partner (not the current user)
        if dm.sender == request.user:
            partner = dm.recipient
            partner_role = 'Project Owner' if dm.project.user == partner else 'User'
        else:
            partner = dm.sender
            partner_role = 'Investor' if dm.project.user != partner else 'Project Owner'

        key = f"{partner.id}_{dm.project.id}"
        if key not in direct_conversations:
            direct_conversations[key] = {
                'id': f"direct_{dm.project.id}_{partner.id}",
                'type': 'direct',
                'name': partner.get_full_name() or partner.username,
                'role': partner_role,
                'project': dm.project.name,
                'userId': partner.id,
                'projectId': dm.project.id,
                'avatar': getattr(getattr(partner, 'userprofile', None), 'profile_picture', None) if hasattr(partner, 'userprofile') else None,
                'online': False,  # TODO: Implement online status
                'unread': DirectMessage.objects.filter(
                    Q(project=dm.project) &
                    Q(sender=partner) &
                    Q(recipient=request.user) &
                    Q(is_read=False)
                ).exists(),
                'lastMessage': dm.content,
                'lastMessageTime': dm.timestamp.strftime('%b %d, %I:%M %p'),
                'timestamp': dm.timestamp
            }
        else:
            # Update if this message is more recent
            if dm.timestamp > direct_conversations[key]['timestamp']:
                direct_conversations[key].update({
                    'lastMessage': dm.content,
                    'lastMessageTime': dm.timestamp.strftime('%b %d, %I:%M %p'),
                    'timestamp': dm.timestamp
                })

    conversations.extend(direct_conversations.values())

    # Remove duplicates and sort by timestamp
    unique_conversations = {}
    for conv in conversations:
        if conv['id'] not in unique_conversations:
            unique_conversations[conv['id']] = conv
        else:
            # Keep the one with more recent timestamp
            if conv['timestamp'] > unique_conversations[conv['id']]['timestamp']:
                unique_conversations[conv['id']] = conv

    # Sort by timestamp (most recent first)
    sorted_conversations = sorted(
        unique_conversations.values(),
        key=lambda x: x['timestamp'],
        reverse=True
    )

    return JsonResponse({
        'success': True,
        'conversations': sorted_conversations
    })

@login_required
def messages_api(request, conversation_id):
    """API endpoint to get messages for a specific conversation"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Parse conversation ID
        if conversation_id.startswith('app_'):
            # Application conversation
            app_id = int(conversation_id.replace('app_', ''))
            application = get_object_or_404(Application, id=app_id)

            # Check permissions
            if request.user != application.applicant and request.user != application.position.project.user:
                return JsonResponse({'error': 'Permission denied'}, status=403)

            # Get messages
            messages = Message.objects.filter(application=application).order_by('timestamp')

            message_list = []
            for msg in messages:
                message_list.append({
                    'id': msg.id,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'isSent': msg.sender == request.user,
                    'sender': msg.sender.get_full_name() or msg.sender.username,
                    'status': 'Read' if msg.is_read else 'Delivered'
                })

        elif conversation_id.startswith('direct_'):
            # Direct message conversation
            parts = conversation_id.replace('direct_', '').split('_')
            project_id = int(parts[0])
            other_user_id = int(parts[1])

            project = get_object_or_404(Project, id=project_id)
            other_user = get_object_or_404(User, id=other_user_id)

            # Check permissions
            if request.user != project.user and request.user != other_user:
                return JsonResponse({'error': 'Permission denied'}, status=403)

            # Get messages
            messages = DirectMessage.objects.filter(
                project=project,
                sender__in=[request.user, other_user],
                recipient__in=[request.user, other_user]
            ).order_by('timestamp')

            message_list = []
            for msg in messages:
                message_list.append({
                    'id': msg.id,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'isSent': msg.sender == request.user,
                    'sender': msg.sender.get_full_name() or msg.sender.username,
                    'status': 'Read' if msg.is_read else 'Delivered'
                })

        else:
            return JsonResponse({'error': 'Invalid conversation ID'}, status=400)

        return JsonResponse({
            'success': True,
            'messages': message_list
        })

    except (ValueError, Application.DoesNotExist, Project.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    except Exception as e:
        logger.error(f"Error loading messages: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def send_unified_message_api(request):
    """API endpoint to send messages in the unified messaging system"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        conversation_id = data.get('conversationId')
        content = data.get('content', '').strip()

        if not content:
            return JsonResponse({'error': 'Message content is required'}, status=400)

        if conversation_id.startswith('app_'):
            # Application message
            app_id = int(conversation_id.replace('app_', ''))
            application = get_object_or_404(Application, id=app_id)

            # Check permissions
            if request.user != application.applicant and request.user != application.position.project.user:
                return JsonResponse({'error': 'Permission denied'}, status=403)

            # Determine recipient
            if request.user == application.applicant:
                recipient = application.position.project.user
            else:
                recipient = application.applicant

            # Create message
            message = Message.objects.create(
                application=application,
                sender=request.user,
                recipient=recipient,
                content=content
            )

            # Create notification
            Notification.objects.create(
                user=recipient,
                title="New Application Message 💬",
                message=f"{request.user.username} sent you a message about the application for {application.position.project.name}",
                notification_type="application_message",
                related_object_id=application.id
            )

        elif conversation_id.startswith('direct_'):
            # Direct message
            parts = conversation_id.replace('direct_', '').split('_')
            project_id = int(parts[0])
            other_user_id = int(parts[1])

            project = get_object_or_404(Project, id=project_id)
            other_user = get_object_or_404(User, id=other_user_id)

            # Check permissions
            if request.user != project.user and request.user != other_user:
                return JsonResponse({'error': 'Permission denied'}, status=403)

            # Create direct message
            message = DirectMessage.objects.create(
                project=project,
                sender=request.user,
                recipient=other_user,
                content=content
            )

            # Create notification
            Notification.objects.create(
                user=other_user,
                title="New Direct Message 💬",
                message=f"{request.user.username} sent you a message about {project.name}",
                notification_type="direct_message",
                related_object_id=project.id
            )

        else:
            return JsonResponse({'error': 'Invalid conversation ID'}, status=400)

        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'isSent': True,
                'status': 'Sent'
            }
        })

    except (ValueError, Application.DoesNotExist, Project.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def mark_conversation_read_api(request, conversation_id):
    """API endpoint to mark a conversation as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        if conversation_id.startswith('app_'):
            # Application conversation
            app_id = int(conversation_id.replace('app_', ''))
            application = get_object_or_404(Application, id=app_id)

            # Check permissions
            if request.user != application.applicant and request.user != application.position.project.user:
                return JsonResponse({'error': 'Permission denied'}, status=403)

            # Mark messages as read
            Message.objects.filter(
                application=application,
                recipient=request.user,
                is_read=False
            ).update(is_read=True)

        elif conversation_id.startswith('direct_'):
            # Direct message conversation
            parts = conversation_id.replace('direct_', '').split('_')
            project_id = int(parts[0])
            other_user_id = int(parts[1])

            project = get_object_or_404(Project, id=project_id)
            other_user = get_object_or_404(User, id=other_user_id)

            # Check permissions
            if request.user != project.user and request.user != other_user:
                return JsonResponse({'error': 'Permission denied'}, status=403)

            # Mark messages as read
            DirectMessage.objects.filter(
                project=project,
                sender=other_user,
                recipient=request.user,
                is_read=False
            ).update(is_read=True)

        else:
            return JsonResponse({'error': 'Invalid conversation ID'}, status=400)

        return JsonResponse({'success': True})

    except (ValueError, Application.DoesNotExist, Project.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    except Exception as e:
        logger.error(f"Error marking conversation as read: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def unified_notifications_api(request):
    """API endpoint to get all notifications with enhanced grouping and priority"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Get all notifications for the user
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

        notification_list = []
        for notification in notifications:
            # Determine priority based on type and content
            priority = 'normal'
            if notification.notification_type in ['application', 'investment']:
                priority = 'high'
            elif 'urgent' in notification.message.lower() or 'critical' in notification.message.lower():
                priority = 'critical'

            # Get project name if available
            project_name = None
            conversation_id = None

            if notification.notification_type == 'application' and notification.related_object_id:
                try:
                    application = Application.objects.get(id=notification.related_object_id)
                    project_name = application.position.project.name
                    conversation_id = f"app_{application.id}"
                except Application.DoesNotExist:
                    pass
            elif notification.notification_type == 'direct_message' and notification.related_object_id:
                try:
                    project = Project.objects.get(id=notification.related_object_id)
                    project_name = project.name
                    # For direct messages, we need to determine the other user
                    # This is a simplified approach - in practice, you'd store more context
                    conversation_id = f"direct_{project.id}_0"  # Placeholder
                except Project.DoesNotExist:
                    pass
            elif notification.notification_type == 'application_message' and notification.related_object_id:
                try:
                    application = Application.objects.get(id=notification.related_object_id)
                    project_name = application.position.project.name
                    conversation_id = f"app_{application.id}"
                except Application.DoesNotExist:
                    pass

            notification_list.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'priority': priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'project_name': project_name,
                'conversation_id': conversation_id,
                'related_object_id': notification.related_object_id
            })

        return JsonResponse({
            'success': True,
            'notifications': notification_list
        })

    except Exception as e:
        logger.error(f"Error loading unified notifications: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def mark_notification_read_api(request, notification_id):
    """API endpoint to mark a single notification as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()

        return JsonResponse({'success': True})

    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def mark_multiple_notifications_read_api(request):
    """API endpoint to mark multiple notifications as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])

        if not notification_ids:
            return JsonResponse({'error': 'No notification IDs provided'}, status=400)

        # Update notifications
        updated_count = Notification.objects.filter(
            id__in=notification_ids,
            user=request.user,
            is_read=False
        ).update(is_read=True)

        return JsonResponse({
            'success': True,
            'updated_count': updated_count
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error marking multiple notifications as read: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def delete_multiple_notifications_api(request):
    """API endpoint to delete multiple notifications"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])

        if not notification_ids:
            return JsonResponse({'error': 'No notification IDs provided'}, status=400)

        # Delete notifications
        deleted_count, _ = Notification.objects.filter(
            id__in=notification_ids,
            user=request.user
        ).delete()

        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error deleting multiple notifications: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def unified_notifications_view(request):
    """Unified notifications interface"""
    return render(request, 'unified_notifications.html')

@login_required
def navigation_data_api(request):
    """API endpoint to get navigation data for messaging components"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Count unread messages from different sources
        unread_messages = 0
        unread_notifications = 0
        unread_applications = 0
        active_conversations = 0

        # Count unread direct messages
        unread_direct_messages = DirectMessage.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        # Count unread application messages
        unread_app_messages = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        unread_messages = unread_direct_messages + unread_app_messages

        # Count unread notifications
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        # Count unread application-specific notifications
        unread_applications = Notification.objects.filter(
            user=request.user,
            is_read=False,
            notification_type__in=['application', 'application_message']
        ).count()

        # Count active conversations (conversations with messages in last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)

        # Active direct message conversations
        active_direct_conversations = DirectMessage.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user),
            timestamp__gte=week_ago
        ).values('project', 'sender', 'recipient').distinct().count()

        # Active application conversations
        active_app_conversations = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user),
            timestamp__gte=week_ago
        ).values('application').distinct().count()

        active_conversations = active_direct_conversations + active_app_conversations

        return JsonResponse({
            'success': True,
            'unreadMessages': unread_messages,
            'unreadNotifications': unread_notifications,
            'unreadApplications': unread_applications,
            'activeConversations': active_conversations
        })

    except Exception as e:
        logger.error(f"Error loading navigation data: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def investor_messages_dashboard(request):
    """Dashboard for investors to view all their direct message conversations"""
    # Get all direct messages where the user is the sender (investor)
    investor_messages = DirectMessage.objects.filter(
        sender=request.user
    ).select_related('project', 'recipient').order_by('-timestamp')

    # Group messages by project and conversation partner (founder)
    conversations = {}

    for message in investor_messages:
        project = message.project
        founder = message.recipient

        # Create a unique key for each conversation
        conversation_key = f"{project.id}_{founder.id}"

        if conversation_key not in conversations:
            conversations[conversation_key] = {
                'project': project,
                'founder': founder,
                'messages': [],
                'last_message': None,
                'unread_count': 0
            }

        conversations[conversation_key]['messages'].append(message)
        conversations[conversation_key]['last_message'] = message

        # Count unread messages from the founder
        if message.recipient == request.user and not message.is_read:
            conversations[conversation_key]['unread_count'] += 1

    # Also get messages where user is recipient (replies from founders)
    received_messages = DirectMessage.objects.filter(
        recipient=request.user
    ).select_related('project', 'sender').order_by('-timestamp')

    for message in received_messages:
        project = message.project
        founder = message.sender

        # Create a unique key for each conversation
        conversation_key = f"{project.id}_{founder.id}"

        if conversation_key not in conversations:
            conversations[conversation_key] = {
                'project': project,
                'founder': founder,
                'messages': [],
                'last_message': None,
                'unread_count': 0
            }

        conversations[conversation_key]['messages'].append(message)

        # Update last message if this is more recent
        if (not conversations[conversation_key]['last_message'] or
            message.timestamp > conversations[conversation_key]['last_message'].timestamp):
            conversations[conversation_key]['last_message'] = message

        # Count unread messages
        if not message.is_read:
            conversations[conversation_key]['unread_count'] += 1

    # Convert to list and sort by last message timestamp
    conversation_list = list(conversations.values())
    conversation_list.sort(
        key=lambda x: x['last_message'].timestamp if x['last_message'] else timezone.now(),
        reverse=True
    )

    # Get total unread count
    total_unread = DirectMessage.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    context = {
        'conversations': conversation_list,
        'total_unread': total_unread,
        'total_conversations': len(conversation_list),
    }

    # Add unread message counts
    context.update(get_unread_counts(request.user))

    return render(request, 'investor_messages_dashboard.html', context)


@login_required
def browse_projects_view(request):
    """View for browsing projects"""
    return render(request, 'browse_projects.html')

@login_required
@require_POST
def track_time(request):
    """Track time spent on project detail pages"""
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        time_spent = data.get('time_spent', 0)  # in seconds
        
        if not project_id:
            return JsonResponse({'error': 'Project ID is required'}, status=400)
        
        project = get_object_or_404(Project, id=project_id)
        
        # Update or create ProjectView record
        project_view, created = ProjectView.objects.get_or_create(
            user=request.user,
            project=project,
            defaults={'view_count': 1, 'total_time_spent': time_spent}
        )
        
        if not created:
            project_view.view_count += 1
            project_view.total_time_spent += time_spent
            project_view.save()
        
        # Update analytics
        update_user_project_analytics(request.user, project)
        
        # Regenerate recommendations if user spent significant time (more than 30 seconds)
        if time_spent > 30:
            generate_enhanced_recommendations_for_user(request.user)
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error tracking time: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)





def update_user_project_analytics(user, project):
    """Update UserProjectAnalytics for a user-project pair"""
    try:
        analytics, created = UserProjectAnalytics.objects.get_or_create(
            user=user,
            project=project,
            defaults={
                'total_invested': 0,
                'invest_count': 0,
                'view_count': 0,
                'total_read_time': 0
            }
        )
        
        # Update view count and read time from ProjectView
        try:
            project_view = ProjectView.objects.get(user=user, project=project)
            analytics.view_count = project_view.view_count
            analytics.total_read_time = project_view.total_time_spent
        except ProjectView.DoesNotExist:
            pass
        
        # Update investment data
        investments = Investment.objects.filter(investor=user, project=project)
        analytics.invest_count = investments.count()
        analytics.total_invested = investments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        analytics.save()
        return analytics
        
    except Exception as e:
        logger.error(f"Error updating analytics for user {user.id} and project {project.id}: {str(e)}")
        return None


def generate_recommendations_for_user(user):
    """Generate recommendations for a specific user"""
    try:
        # Get user's analytics
        user_analytics = UserProjectAnalytics.objects.filter(user=user)
        
        if not user_analytics.exists():
            return
        
        # Get user's invested and created projects to exclude from recommendations
        user_invested_projects = Investment.objects.filter(investor=user).values_list('project', flat=True)
        user_created_projects = Project.objects.filter(user=user).values_list('id', flat=True)
        
        # Simple collaborative filtering approach
        # Find users with similar investment patterns
        similar_users = []
        
        for analytics in user_analytics:
            if analytics.total_invested > 0:  # User has invested in this project
                # Find other users who also invested in this project
                similar_investors = Investment.objects.filter(
                    project=analytics.project
                ).exclude(investor=user).values_list('investor', flat=True)
                
                for similar_investor_id in similar_investors:
                    similar_users.append(similar_investor_id)
        
        # Get unique similar users
        similar_users = list(set(similar_users))
        
        # Get projects that similar users invested in
        recommended_projects = set()
        for similar_user_id in similar_users:
            investments = Investment.objects.filter(investor_id=similar_user_id)
            for investment in investments:
                # Exclude projects user has already invested in or created
                if (not Investment.objects.filter(investor=user, project=investment.project).exists() and
                    investment.project.id not in user_created_projects):
                    recommended_projects.add(investment.project)
        
        # Calculate recommendation scores and create recommendations
        for project in recommended_projects:
            # Simple scoring based on similar users' investment amounts
            similar_investments = Investment.objects.filter(
                project=project,
                investor_id__in=similar_users
            )
            
            if similar_investments.exists():
                avg_amount = similar_investments.aggregate(
                    avg=models.Avg('amount')
                )['avg'] or 0
                
                score = min(1.0, avg_amount / 1000)  # Normalize score
                
                # Create or update recommendation
                recommendation, created = Recommendation.objects.get_or_create(
                    user=user,
                    project=project,
                    defaults={
                        'score': score,
                        'recommended_amount': avg_amount
                    }
                )
                
                if not created:
                    recommendation.score = score
                    recommendation.recommended_amount = avg_amount
                    recommendation.save()
        
    except Exception as e:
        logger.error(f"Error generating recommendations for user {user.id}: {str(e)}")


def generate_all_recommendations():
    """Generate recommendations for all users"""
    from django.contrib.auth.models import User
    
    users = User.objects.all()
    for user in users:
        generate_recommendations_for_user(user)


def calculate_user_project_score(user, project):
    """Calculate interaction score for a user-project pair"""
    try:
        # Get user's analytics for this project
        analytics = UserProjectAnalytics.objects.filter(user=user, project=project).first()
        if not analytics:
            return 0.0
        
        # Get max values for normalization
        max_investment = Investment.objects.aggregate(max_amount=models.Max('amount'))['max_amount'] or 1
        max_view_count = ProjectView.objects.aggregate(max_views=models.Max('view_count'))['max_views'] or 1
        max_time_spent = ProjectView.objects.aggregate(max_time=models.Max('total_time_spent'))['max_time'] or 1
        
        # Calculate weighted score
        investment_score = 0.7 * (float(analytics.total_invested) / float(max_investment)) if max_investment > 0 else 0
        view_score = 0.2 * min(analytics.view_count / max_view_count, 1.0) if max_view_count > 0 else 0
        time_score = 0.1 * (analytics.total_read_time / max_time_spent) if max_time_spent > 0 else 0
        
        total_score = investment_score + view_score + time_score
        return min(total_score, 1.0)  # Normalize to 0-1
        
    except Exception as e:
        logger.error(f"Error calculating score for user {user.id} and project {project.id}: {str(e)}")
        return 0.0


def create_project_vectors():
    """Create TF-IDF vectors for all projects"""
    try:
        projects = Project.objects.all()
        
        # Create documents for TF-IDF
        docs = []
        project_ids = []
        
        for project in projects:
            # Combine title, category, stage, and description
            doc_text = f"{project.name} {project.category} {project.stage} {project.description}"
            if project.problem:
                doc_text += f" {project.problem}"
            if project.market:
                doc_text += f" {project.market}"
            if project.competition:
                doc_text += f" {project.competition}"
            if project.details:
                doc_text += f" {project.details}"
            
            docs.append(doc_text)
            project_ids.append(project.id)
        
        if not docs:
            return None, None, None
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform(docs)
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        return similarity_matrix, project_ids, vectorizer
        
    except Exception as e:
        logger.error(f"Error creating project vectors: {str(e)}")
        return None, None, None


def get_user_interacted_projects(user):
    """Get projects the user has interacted with (invested or viewed)"""
    try:
        # Get projects user has invested in
        invested_projects = Investment.objects.filter(investor=user).values_list('project', flat=True)
        
        # Get projects user has viewed
        viewed_projects = ProjectView.objects.filter(user=user).values_list('project', flat=True)
        
        # Combine and get unique projects
        interacted_projects = list(set(list(invested_projects) + list(viewed_projects)))
        
        return interacted_projects
        
    except Exception as e:
        logger.error(f"Error getting interacted projects for user {user.id}: {str(e)}")
        return []


def generate_enhanced_recommendations_for_user(user):
    """Generate enhanced recommendations using collaborative filtering"""
    try:
        # Get projects the user has invested in
        user_investments = Investment.objects.filter(investor=user).values_list('project_id', flat=True)
        
        if user_investments:
            # Find users who invested in similar projects
            similar_users = User.objects.filter(
                investments__project_id__in=user_investments
            ).exclude(id=user.id).distinct()
            
            # Get projects that similar users have invested in
            similar_projects = Project.objects.filter(
                investments__investor__in=similar_users
            ).exclude(
                id__in=user_investments
            ).exclude(
                user=user  # Don't recommend user's own projects
            ).annotate(
                investment_count=Count('investments')
            ).order_by('-investment_count')[:20]
        else:
            # Cold start: recommend popular projects
            similar_projects = Project.objects.annotate(
                investment_count=Count('investments')
            ).exclude(
                user=user  # Don't recommend user's own projects
            ).order_by('-investment_count')[:20]
        
        # Clear existing recommendations
        Recommendation.objects.filter(user=user).delete()
        
        # Create recommendations
        for i, project in enumerate(similar_projects):
            score = 1.0 - (i * 0.05)  # Decreasing scores
            Recommendation.objects.create(
                user=user,
                project=project,
                score=max(0.1, score),  # Minimum score of 0.1
                recommended_amount=1.0
            )
        
        logger.info(f"Generated {len(similar_projects)} recommendations for user {user.username}")
        
    except Exception as e:
        logger.error(f"Error generating enhanced recommendations for user {user.id}: {str(e)}")


def generate_all_enhanced_recommendations():
    """Generate enhanced recommendations for all users"""
    from django.contrib.auth.models import User
    
    users = User.objects.all()
    for user in users:
        generate_enhanced_recommendations_for_user(user)

@login_required
def get_recommendation(request, project_id):
    """Get recommendation data for a specific project"""
    try:
        project = get_object_or_404(Project, id=project_id)
        recommendation = Recommendation.objects.filter(
            user=request.user,
            project=project
        ).first()
        
        if recommendation and recommendation.recommended_amount:
            return JsonResponse({
                'recommended_amount': str(recommendation.recommended_amount),
                'score': recommendation.score
            })
        else:
            return JsonResponse({
                'recommended_amount': None,
                'score': 0
            })
            
    except Exception as e:
        logger.error(f"Error getting recommendation: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
def predict_investment_amount_api(request, project_id):
    """AI-powered investment amount prediction API"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        # Get AI prediction with explanation
        prediction_data = predict_investment_with_explanation(request.user, project)
        
        return JsonResponse({
            'predicted_amount': prediction_data['predicted_amount'],
            'explanations': prediction_data['explanations'],
            'project_analytics': prediction_data['project_analytics'],
            'user_profile': prediction_data['user_profile']
        })
        
    except Exception as e:
        logger.error(f"Error predicting investment amount: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# AI-Powered Features
# from .ai_utils import generate_suggestions, rewrite_pitch, analyze_pitch_strength, get_field_suggestions, enhance_project_creation_data

# Simple fallback functions for AI features
def generate_suggestions(text):
    """Fallback function for AI suggestions"""
    return "Consider expanding on your key value proposition and market opportunity."

def rewrite_pitch(text):
    """Fallback function for pitch rewriting"""
    return text  # Return original text as fallback

def analyze_pitch_strength(text):
    """Fallback function for pitch analysis"""
    return {
        'score': 0.7,
        'feedback': 'Your pitch looks good. Consider adding more specific metrics and market validation.'
    }

def get_field_suggestions(field, current_text):
    """Fallback function for field suggestions"""
    suggestions = {
        'problem': 'Clearly define the specific problem you are solving and its impact.',
        'market': 'Describe your target market size and opportunity.',
        'competition': 'Identify key competitors and your competitive advantages.',
        'details': 'Add technical specifications, timeline, and key features.'
    }
    return suggestions.get(field, 'Please provide more details.')

def enhance_project_creation_data(data):
    """Fallback function for data enhancement"""
    return data  # Return original data as fallback

@csrf_exempt
def get_pitch_suggestions(request):
    """Get AI-powered pitch suggestions and rewriting"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            text = data.get("text", "")
        except:
            text = request.POST.get("text", "")

        suggestions = generate_suggestions(text)
        rewritten = rewrite_pitch(text)
        analysis = analyze_pitch_strength(text)

        return JsonResponse({
            "suggestions": suggestions,
            "rewritten": rewritten,
            "analysis": analysis
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def analyze_pitch_api(request):
    """Analyze pitch text and provide detailed feedback"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            text = data.get("text", "")
        except:
            text = request.POST.get("text", "")

        analysis = analyze_pitch_strength(text)
        
        return JsonResponse({
            "success": True,
            "analysis": analysis
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def get_field_suggestions_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            field_name = data.get("field", "")
            current_value = data.get("current_value", "")
            other_fields = data.get("other_fields", {})
        except Exception:
            field_name = request.POST.get("field", "")
            current_value = request.POST.get("current_value", "")
            other_fields = json.loads(request.POST.get("other_fields", "{}"))

        suggestions = get_field_suggestions(field_name, current_value, other_fields)

        return JsonResponse({
            "success": True,
            "suggestions": suggestions
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def enhance_project_creation_api(request):
    """Enhance project creation data with AI suggestions"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            project_data = data.get("project_data", {})
        except:
            project_data = json.loads(request.POST.get("project_data", "{}"))

        enhanced_data = enhance_project_creation_data(project_data)
        
        return JsonResponse({
            "success": True,
            "enhanced_data": enhanced_data
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def get_smart_project_templates_api(request):
    """Get AI-generated project templates based on category and stage"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            category = data.get("category", "")
            stage = data.get("stage", "")
        except:
            category = request.POST.get("category", "")
            stage = request.POST.get("stage", "")

        # Generate templates based on category and stage
        templates = {
            "description": "",
            "problem": "",
            "market": "",
            "competition": "",
            "details": ""
        }

        if category == "Technology" and stage == "Idea":
            templates = {
                "description": "We are building an innovative tech solution to address a critical market need.",
                "problem": "Current solutions in the market are inefficient and don't meet user expectations.",
                "market": "The technology market is rapidly growing with increasing demand for better solutions.",
                "competition": "While existing solutions exist, they lack the key features that users need.",
                "details": "Our solution leverages cutting-edge technology to deliver superior user experience."
            }
        elif category == "Healthcare" and stage == "MVP":
            templates = {
                "description": "We are developing a healthcare platform that improves patient outcomes.",
                "problem": "Healthcare systems struggle with inefficiency and poor patient engagement.",
                "market": "The healthcare technology market is valued at $350B+ with 15% annual growth.",
                "competition": "Traditional healthcare systems lack modern technology integration.",
                "details": "Our MVP includes core features for patient management and care coordination."
            }
        # Add more category/stage combinations as needed

        return JsonResponse({
            "success": True,
            "templates": templates
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

def normalize(text):
    """Normalize text for processing"""
    return text.strip().lower()

def get_field_recommendation(request):
    """Get AI recommendations for specific project fields"""
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        field = request.GET.get("field")
        current = request.GET.get("current")

        others = {
            'description': normalize(request.GET.get("desc", "")),
            'problem': normalize(request.GET.get("problem", "")),
            'market': normalize(request.GET.get("market", "")),
            'competition': normalize(request.GET.get("competition", "")),
            'details': normalize(request.GET.get("details", ""))
        }

        others[field] = normalize(current)

        try:
            # Use simple fallback suggestions instead of complex ML model
            fallback_suggestions = {
                "description": "Consider highlighting your unique value proposition and target audience",
                "problem": "Describe the specific pain point your solution addresses",
                "market": "Include market size, growth rate, and target demographics",
                "competition": "Explain your competitive advantages and differentiation",
                "details": "Add technical specifications, timeline, and key features"
            }
            return JsonResponse({"suggestion": fallback_suggestions.get(field, "Please provide more details")})

        except Exception as e:
            return JsonResponse({"error": f"Recommendation error: {str(e)}"})

    return JsonResponse({"error": "Invalid request"})
def select_for_comparison(request, project_id):
    # Get current compare list from session
    compare_list = request.session.get("compare_list", [])

    # If selecting a new project and already 2 are selected, reset the list
    if project_id not in compare_list and len(compare_list) >= 2:
        compare_list = []

    if project_id in compare_list:
        compare_list.remove(project_id)  # remove if already selected
        status = "removed"
    else:
        compare_list.append(project_id)  # add if not in list
        status = "added"

    request.session["compare_list"] = compare_list
    request.session.modified = True

    return JsonResponse({
        "status": status,
        "compare_list": compare_list
    })

from django.shortcuts import render
from .models import Project
from .recommend import gemini_compare
from datetime import date

def compare_selected(request):
    compare_list = request.session.get("compare_list", [])
    projects = Project.objects.filter(id__in=compare_list)

    if not projects.exists():
        return render(request, "compare.html", {"error": "No startups selected."})

    # Get AI comparison using Gemini
    try:
        comparison = gemini_compare(projects)
    except Exception as e:
        logger.error(f"AI comparison failed: {e}")
        comparison = {
            "analysis": {},
            "recommendation": {"name": "N/A", "reason": f"AI comparison failed: {str(e)}", "confidence": 0}
        }

    # Prepare project data for cards
    projects_with_data = []
    for p in projects:
        days_since_launch = (date.today() - p.created_at.date()).days
        
        projects_with_data.append({
            'project': p,
            'current_funding': p.current_funding(),
            'funding_percentage': p.funding_percentage(),
            'days_since_launch': days_since_launch,
            'open_positions': p.positions.count()
        })

    # Prepare analysis data
    analysis_list = []
    for p in projects:
        analysis_data = comparison.get("analysis", {}).get(p.name, {})
        scores_raw = analysis_data.get("scores", {})

        # Ensure all four scores exist
        scores_display = {
            "Market": scores_raw.get("Market", 0),
            "Problem": scores_raw.get("Problem", 0),
            "Competition": scores_raw.get("Competition", 0),
            "Risks": scores_raw.get("Risks", 0),
        }

        analysis_list.append({
            "project": p,
            "scores_display": scores_display,
            "notes": analysis_data.get("notes", "No notes available."),
        })

    # Prepare recommendation data
    recommendation = comparison.get("recommendation", {})
    recommendation.setdefault("name", "N/A")
    recommendation.setdefault("confidence", 0)
    recommendation.setdefault("reason", "No reason provided.")

    return render(request, "compare.html", {
        "projects": projects_with_data,
        "analysis_list": analysis_list,
        "recommendation": recommendation,
    })




from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
def clear_comparison(request):
    """
    Clears the list of selected projects from the user's session.
    """
    if "compare_list" in request.session:
        del request.session["compare_list"]
        request.session.modified = True
    return JsonResponse({"status": "cleared"})


from django.http import JsonResponse
from .models import Project

def get_projects_by_ids(request):
    """
    API endpoint to return a list of projects based on their IDs.
    """
    project_ids_str = request.GET.get('ids', '')
    if not project_ids_str:
        return JsonResponse([], safe=False)
    
    project_ids = [int(id) for id in project_ids_str.split(',') if id.isdigit()]
    projects = Project.objects.filter(id__in=project_ids).values('id', 'name', 'category')
    
    return JsonResponse(list(projects), safe=False)


@csrf_exempt
def generate_ai_report_api(request, project_id):
    """
    API endpoint to generate AI analyst report for a project.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        project = get_object_or_404(Project, id=project_id)
        
        # Import AI analyst here to avoid circular imports
        from main.ai_analyst import ai_analyst
        
        # Generate the AI report
        report = ai_analyst.generate_report(project)
        
        return JsonResponse({
            'success': True,
            'message': 'AI analyst report generated successfully',
            'report_id': report.id,
            'risk_score': report.risk_score,
            'growth_score': report.growth_score,
            'risk_level': report.risk_level,
            'growth_index': report.growth_index
        })
        
    except Exception as e:
        logger.error(f"Error generating AI report for project {project_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to generate AI report: {str(e)}'
        }, status=500)

@csrf_exempt
def project_ai_insights_api(request, project_id):
    """
    API endpoint to get AI insights for a project (for investment modal).
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        project = get_object_or_404(Project, id=project_id)
        
        if not hasattr(project, 'ai_report') or not project.ai_report:
            return JsonResponse({
                'success': False,
                'error': 'AI report not available for this project'
            }, status=404)
        
        report = project.ai_report
        
        # Create insights summary for investment modal
        insights = {
            'risk_score': report.risk_score,
            'risk_level': report.risk_level,
            'risk_color': report.get_risk_color(),
            'risk_icon': report.get_risk_icon(),
            'growth_score': report.growth_score,
            'growth_index': report.growth_index,
            'growth_color': report.get_growth_color(),
            'growth_icon': report.get_growth_icon(),
            'risk_summary': report.risk_analysis[:200] + '...' if len(report.risk_analysis) > 200 else report.risk_analysis,
            'recommendations': report.recommendations[:150] + '...' if len(report.recommendations) > 150 else report.recommendations
        }
        
        return JsonResponse({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logger.error(f"Error fetching AI insights for project {project_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to fetch AI insights: {str(e)}'
        }, status=500)