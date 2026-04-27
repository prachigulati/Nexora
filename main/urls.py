from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # No login required for home
    path('login/', views.login_page, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('apply/', views.submit_application, name='submit_application'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('save-transaction/', views.save_transaction, name='save_transaction'),
    path('project-funding/<int:project_id>/', views.get_project_funding, name='project_funding'),
    path('api/chat/', views.chatbot_api, name='chat_api'),
    path('blog/', views.blog, name='blog'),
    path('messages/history/<int:application_id>/', views.message_history, name='message_history'),
    path('messages/send/', views.send_message, name='send_message'),
    path('chatbot-api/', views.chatbot_api, name='chatbot_api'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('applicant/messages/', views.applicant_messages_view, name='applicant_messages'),
    path('applications/update_status/', views.update_application_status, name='update_application_status'),
    # New pages
    path('about/', views.about, name='about'),
    path('features/', views.features, name='features'),
    path('contact/', views.contact, name='contact'),
    # User pages
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    # AI Mentorship
    path('ai-mentorship/', views.ai_mentorship, name='ai_mentorship'),
    path('ai-mentorship-api/', views.ai_mentorship_api, name='ai_mentorship_api'),
    path('ai-mentorship-history/', views.ai_mentorship_history, name='ai_mentorship_history'),
    # Analytics and Network
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('network/', views.network_explorer, name='network_explorer'),
    # Data Export
    path('export-data/', views.export_user_data, name='export_user_data'),
    # Notifications
    path('notifications/mark-all-read/', views.mark_notifications_read, name='mark_notifications_read'),
    # P2P Direct Chat
    path('direct-chat/<int:project_id>/', views.direct_chat_view, name='direct_chat'),
    path('send-direct-message/', views.send_direct_message, name='send_direct_message'),
    # Unified Messaging System
    path('messaging/', views.unified_messaging_view, name='unified_messaging'),
    path('api/conversations/', views.conversations_api, name='conversations_api'),
    path('api/messages/<str:conversation_id>/', views.messages_api, name='messages_api'),
    path('api/send-message/', views.send_unified_message_api, name='send_unified_message_api'),
    path('api/conversations/<str:conversation_id>/mark-read/', views.mark_conversation_read_api, name='mark_conversation_read_api'),
    # Unified Notification System
    path('notifications-center/', views.unified_notifications_view, name='unified_notifications'),
    path('api/unified-notifications/', views.unified_notifications_api, name='unified_notifications_api'),
    path('api/notifications/<int:notification_id>/mark-read/', views.mark_notification_read_api, name='mark_notification_read_api'),
    path('api/notifications/mark-multiple-read/', views.mark_multiple_notifications_read_api, name='mark_multiple_notifications_read_api'),
    path('api/notifications/delete-multiple/', views.delete_multiple_notifications_api, name='delete_multiple_notifications_api'),
    # Navigation Data API
    path('api/navigation-data/', views.navigation_data_api, name='navigation_data_api'),
    path('direct-messages/<int:project_id>/', views.get_direct_messages, name='get_direct_messages'),
    path('messages-dashboard/', views.direct_messages_dashboard, name='direct_messages_dashboard'),
    path('my-messages/', views.investor_messages_dashboard, name='investor_messages_dashboard'),
    path('browse-projects/', views.browse_projects_view, name='browse_projects'),
    path('direct-messages-dashboard/', views.direct_messages_dashboard, name='direct_messages_dashboard'),
    # New tracking and recommendation URLs
    path('api/track-time/', views.track_time, name='track_time'),
    path('api/recommendation/<int:project_id>/', views.get_recommendation, name='get_recommendation'),
    path('api/predict-investment/<int:project_id>/', views.predict_investment_amount_api, name='predict_investment_amount_api'),
    # AI-Powered Features
    path('get_ai_suggestion/', views.get_pitch_suggestions, name='get_ai_suggestion'),
    path('get_field_recommendation/', views.get_field_recommendation, name='get_field_recommendation'),
    
    # Enhanced AI-Powered Features
    path('api/analyze-pitch/', views.analyze_pitch_api, name='analyze_pitch_api'),
    path('api/field-suggestions/', views.get_field_suggestions_api, name='get_field_suggestions_api'),
    path('api/enhance-project-creation/', views.enhance_project_creation_api, name='enhance_project_creation_api'),
    path('api/smart-templates/', views.get_smart_project_templates_api, name='get_smart_project_templates_api'),
    path("select-for-comparison/<int:project_id>/", views.select_for_comparison, name="select_for_comparison"),
    path("compare-selected/", views.compare_selected, name="compare_selected"),
    path('clear-comparison/', views.clear_comparison, name='clear_comparison'),
    path('api/projects/', views.get_projects_by_ids, name='get_projects_by_ids'),
    path('api/generate-ai-report/<int:project_id>/', views.generate_ai_report_api, name='generate_ai_report_api'),
    path('api/project-ai-insights/<int:project_id>/', views.project_ai_insights_api, name='project_ai_insights_api'),
]
