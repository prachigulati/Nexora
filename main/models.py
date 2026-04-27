from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=10, blank=True)  # For phone code
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    company = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    project_updates = models.BooleanField(default=True)
    investment_alerts = models.BooleanField(default=True)
    marketing_communications = models.BooleanField(default=False)

    # Privacy settings
    profile_visibility = models.CharField(max_length=20, choices=[
        ('public', 'Public'),
        ('registered', 'Registered Users'),
        ('private', 'Private')
    ], default='public')
    show_activity_status = models.BooleanField(default=True)
    show_investment_history = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_full_name(self):
        return self.user.get_full_name() or self.user.username

    def get_projects_count(self):
        return self.user.project_set.count()

    def get_total_funded(self):
        """Get total amount this user has received from investors"""
        from django.db.models import Sum
        total = Transaction.objects.filter(project__user=self.user).aggregate(Sum('amount_eth'))
        return total['amount_eth__sum'] or 0

    def get_investments_made(self):
        """Get total amount this user has invested in other projects"""
        from django.db.models import Sum
        total = Transaction.objects.filter(user=self.user).aggregate(Sum('amount_eth'))
        return total['amount_eth__sum'] or 0

    def get_investments_count(self):
        """Get number of investments this user has made"""
        return Transaction.objects.filter(user=self.user).count()

    def get_funded_projects_count(self):
        """Get number of projects this user has funded"""
        return Transaction.objects.filter(user=self.user).values('project').distinct().count()

    def get_success_rate(self):
        """Calculate success rate based on projects that reached their funding goal"""
        total_projects = self.get_projects_count()
        if total_projects == 0:
            return 0

        successful_projects = 0
        for project in self.user.project_set.all():
            if project.current_funding() >= project.funding_goal:
                successful_projects += 1

        return round((successful_projects / total_projects) * 100, 1)

    def get_profile_completion(self):
        """Calculate profile completion percentage and breakdown"""
        completion_data = {
            'basic_info': {'completed': 0, 'total': 0, 'percentage': 0},
            'contact_details': {'completed': 0, 'total': 0, 'percentage': 0},
            'bio_interests': {'completed': 0, 'total': 0, 'percentage': 0},
            'verification': {'completed': 0, 'total': 0, 'percentage': 0},
            'overall': {'completed': 0, 'total': 0, 'percentage': 0}
        }

        # Basic Info (User model fields)
        basic_fields = [
            self.user.first_name,
            self.user.last_name,
            self.user.email,  # Always present for registered users
        ]
        completion_data['basic_info']['total'] = len(basic_fields)
        completion_data['basic_info']['completed'] = sum(1 for field in basic_fields if field and field.strip())
        completion_data['basic_info']['percentage'] = round(
            (completion_data['basic_info']['completed'] / completion_data['basic_info']['total']) * 100
        )

        # Contact Details
        contact_fields = [
            self.phone,
            self.location,
            self.country,
            self.website,
        ]
        completion_data['contact_details']['total'] = len(contact_fields)
        completion_data['contact_details']['completed'] = sum(1 for field in contact_fields if field and field.strip())
        completion_data['contact_details']['percentage'] = round(
            (completion_data['contact_details']['completed'] / completion_data['contact_details']['total']) * 100
        )

        # Bio & Interests
        bio_fields = [
            self.bio,
            self.company,
            self.job_title,
            self.linkedin_url,
            self.twitter_url,
            self.github_url,
            self.avatar,  # Profile picture
        ]
        completion_data['bio_interests']['total'] = len(bio_fields)
        completion_data['bio_interests']['completed'] = sum(1 for field in bio_fields if field and (
            field.strip() if isinstance(field, str) else True
        ))
        completion_data['bio_interests']['percentage'] = round(
            (completion_data['bio_interests']['completed'] / completion_data['bio_interests']['total']) * 100
        )

        # Verification (placeholder for future features)
        verification_fields = [
            # self.email_verified,  # Future feature
            # self.phone_verified,  # Future feature
            # self.identity_verified,  # Future feature
        ]
        completion_data['verification']['total'] = 3  # Placeholder for 3 verification types
        completion_data['verification']['completed'] = 0  # No verification implemented yet
        completion_data['verification']['percentage'] = 0

        # Overall completion
        total_fields = (
            completion_data['basic_info']['total'] +
            completion_data['contact_details']['total'] +
            completion_data['bio_interests']['total'] +
            completion_data['verification']['total']
        )
        total_completed = (
            completion_data['basic_info']['completed'] +
            completion_data['contact_details']['completed'] +
            completion_data['bio_interests']['completed'] +
            completion_data['verification']['completed']
        )

        completion_data['overall']['total'] = total_fields
        completion_data['overall']['completed'] = total_completed
        completion_data['overall']['percentage'] = round((total_completed / total_fields) * 100) if total_fields > 0 else 0

        return completion_data

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        UserProfile.objects.create(user=instance)

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    description = models.TextField(max_length=200)
    problem = models.TextField(max_length=200, blank=True, null=True)
    market = models.TextField(max_length=200, blank=True, null=True)
    competition = models.TextField(max_length=200, blank=True, null=True)
    details = models.TextField(max_length=200, blank=True, null=True)
    stage = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    url = models.URLField(blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', null=True, blank=True)
    funding_goal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def current_funding(self):
        """Calculate total funding received for this project"""
        from django.db.models import Sum
        total = Transaction.objects.filter(project=self).aggregate(Sum('amount_eth'))
        return total['amount_eth__sum'] or 0
    
    def funding_percentage(self):
        """Calculate funding percentage"""
        if self.funding_goal <= 0:
            return 0
        return min(100, int((self.current_funding() / self.funding_goal) * 100))


class Position(models.Model):
    COMPENSATION_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('equity', 'Equity Split'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="positions")
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=200)
    compensation_type = models.CharField(max_length=10, choices=COMPENSATION_CHOICES, default='unpaid')
    def __str__(self):
        return f"{self.title} - {self.project.name}"
    



class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    experience = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.applicant.username} -> {self.position.title}"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Link to Django user
    user_address = models.CharField(max_length=42)  # MetaMask address
    tx_hash = models.CharField(max_length=66, unique=True)
    amount_eth = models.DecimalField(max_digits=10, decimal_places=5)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"{self.amount_eth} ETH from {self.user.username}"
        return f"{self.amount_eth} ETH from {self.user_address[:10]}..."


class Message(models.Model):
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"


# Add the Chat model for the chatbot
class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.message[:30]}'

# AI Mentorship Chat model
class MentorshipChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.username} - Mentorship: {self.message[:30]}'


# Direct Message model for P2P chat between investors and founders
class DirectMessage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='direct_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_direct_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_direct_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Direct message from {self.sender.username} to {self.recipient.username} about {self.project.name}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('application', 'Application'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
        ('message', 'Message'),
        ('direct_message', 'Direct Message'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"


class ProjectView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    view_count = models.IntegerField(default=1)
    total_time_spent = models.FloatField(default=0)  # in seconds
    last_viewed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'project')
        ordering = ['-last_viewed']

    def __str__(self):
        return f"{self.user.username} - {self.project.name}"


class Investment(models.Model):
    investor = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.investor.username} invested {self.amount} in {self.project.name}"


class UserProjectAnalytics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    total_invested = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    invest_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    total_read_time = models.FloatField(default=0)

    class Meta:
        unique_together = ('user', 'project')
        ordering = ['-total_invested']

    def __str__(self):
        return f"{self.user.username} - {self.project.name} Analytics"


class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    score = models.FloatField(default=0)  # Recommendation score
    recommended_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'project')
        ordering = ['-score']

    def __str__(self):
        return f"Recommendation for {self.user.username} - {self.project.name} (Score: {self.score})"


class AIAnalystReport(models.Model):
    """AI-generated analyst report for each startup"""
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='ai_report')
    
    # Risk Analysis
    risk_score = models.FloatField(default=0.0, help_text="Overall risk score (0-100, lower is better)")
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ], default='medium')
    
    # Risk Indicators
    tam_inflation_risk = models.FloatField(default=0.0, help_text="TAM inflation risk (0-100)")
    financial_consistency_risk = models.FloatField(default=0.0, help_text="Financial consistency risk (0-100)")
    market_saturation_risk = models.FloatField(default=0.0, help_text="Market saturation risk (0-100)")
    competition_risk = models.FloatField(default=0.0, help_text="Competition risk (0-100)")
    team_risk = models.FloatField(default=0.0, help_text="Team risk (0-100)")
    
    # Growth Potential
    growth_score = models.FloatField(default=0.0, help_text="Growth potential score (0-100)")
    growth_index = models.CharField(max_length=20, choices=[
        ('low', 'Low Growth'),
        ('medium', 'Medium Growth'),
        ('high', 'High Growth'),
        ('exceptional', 'Exceptional Growth')
    ], default='medium')
    
    # Growth Metrics
    traction_score = models.FloatField(default=0.0, help_text="Traction score (0-100)")
    hiring_momentum = models.FloatField(default=0.0, help_text="Hiring momentum (0-100)")
    market_demand_score = models.FloatField(default=0.0, help_text="Market demand score (0-100)")
    scalability_potential = models.FloatField(default=0.0, help_text="Scalability potential (0-100)")
    
    # Peer Benchmarking
    sector_rank = models.IntegerField(default=0, help_text="Rank within sector (1=best)")
    sector_percentile = models.FloatField(default=0.0, help_text="Percentile within sector (0-100)")
    platform_rank = models.IntegerField(default=0, help_text="Overall platform rank")
    platform_percentile = models.FloatField(default=0.0, help_text="Overall platform percentile (0-100)")
    
    # Benchmarking Scores
    vs_sector_avg = models.FloatField(default=0.0, help_text="Score vs sector average")
    vs_platform_avg = models.FloatField(default=0.0, help_text="Score vs platform average")
    vs_similar_stage = models.FloatField(default=0.0, help_text="Score vs similar stage startups")
    
    # AI Analysis Details
    risk_analysis = models.TextField(blank=True, help_text="Detailed risk analysis")
    growth_analysis = models.TextField(blank=True, help_text="Detailed growth analysis")
    peer_analysis = models.TextField(blank=True, help_text="Detailed peer benchmarking analysis")
    recommendations = models.TextField(blank=True, help_text="AI recommendations for investors")
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    ai_model_version = models.CharField(max_length=50, default='v1.0')
    
    class Meta:
        ordering = ['-growth_score', '-risk_score']
    
    def __str__(self):
        return f"AI Report for {self.project.name} - Risk: {self.risk_level}, Growth: {self.growth_index}"
    
    def get_risk_color(self):
        """Get Bootstrap color class for risk level"""
        colors = {
            'low': 'success',
            'medium': 'warning', 
            'high': 'danger',
            'critical': 'dark'
        }
        return colors.get(self.risk_level, 'secondary')
    
    def get_growth_color(self):
        """Get Bootstrap color class for growth level"""
        colors = {
            'low': 'danger',
            'medium': 'warning',
            'high': 'success', 
            'exceptional': 'primary'
        }
        return colors.get(self.growth_index, 'secondary')
    
    def get_risk_icon(self):
        """Get icon for risk level"""
        icons = {
            'low': 'bi-shield-check',
            'medium': 'bi-shield-exclamation',
            'high': 'bi-shield-x',
            'critical': 'bi-exclamation-triangle'
        }
        return icons.get(self.risk_level, 'bi-shield')
    
    def get_growth_icon(self):
        """Get icon for growth level"""
        icons = {
            'low': 'bi-arrow-down',
            'medium': 'bi-arrow-right',
            'high': 'bi-arrow-up',
            'exceptional': 'bi-rocket'
        }
        return icons.get(self.growth_index, 'bi-arrow-right')