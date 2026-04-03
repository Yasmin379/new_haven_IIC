from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard URLs
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('specialist-dashboard/', views.specialist_dashboard, name='specialist_dashboard'),
    path('profile/', views.user_profile, name='user_profile'),
    
    # Feature URLs
    path('journal/', views.journal_view, name='journal'),
    path('journal/<int:entry_id>/', views.journal_detail, name='journal_detail'),
    path('journal/<int:entry_id>/delete/', views.journal_delete, name='journal_delete'),
    path('mood-check/', views.mood_check_view, name='mood_check'),
    path('study/', views.study_log_view, name='study'),
    path('study-with-me/', views.study_with_me_view, name='study_with_me'),
    path('booking/', views.booking_view, name='booking'),
    path('chat/', views.chat_view, name='chat'),
    path('relax/', views.relax, name='relax'),
    path('preview/', views.user_dashboard, name='preview'),

    
    # API Endpoints
    path('api/chat/', views.chat_with_ai, name='chat_api'),
    path('api/chat-history/', views.chat_history_api, name='chat_history_api'),
    path('api/counselors/', views.get_counselors, name='counselors_api'),
    path('api/my-sessions/', views.api_my_sessions, name='my_sessions_api'),
    path('api/booking-requests/', views.api_booking_requests, name='booking_requests_api'),
    path('api/booking-requests/<int:booking_id>/status/', views.api_update_booking_status, name='booking_status_api'),
    path('api/sessions-data/', views.api_sessions_data, name='sessions_data_api'),
    
    # Homepage / Landing
    path('', views.landing, name='home'),
    path('landing/', views.landing, name='landing'),
]