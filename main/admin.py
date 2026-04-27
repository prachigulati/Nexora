from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Project, Position, Application, Message, Notification, ProjectView, Investment, UserProjectAnalytics, Recommendation
# Unregister the default User admin
admin.site.unregister(User)

# Register it again (optionally with custom admin)
admin.site.register(User, UserAdmin)
admin.site.register(Project)
admin.site.register(Position)
admin.site.register(Application)
admin.site.register(Message)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']

@admin.register(ProjectView)
class ProjectViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'view_count', 'total_time_spent', 'last_viewed']
    list_filter = ['last_viewed']
    search_fields = ['user__username', 'project__name']
    readonly_fields = ['last_viewed']

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['investor', 'project', 'amount', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['investor__username', 'project__name']
    readonly_fields = ['timestamp']

@admin.register(UserProjectAnalytics)
class UserProjectAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'total_invested', 'invest_count', 'view_count', 'total_read_time']
    list_filter = ['total_invested', 'invest_count', 'view_count']
    search_fields = ['user__username', 'project__name']

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'score', 'recommended_amount', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['user__username', 'project__name']
    readonly_fields = ['created_at', 'updated_at']