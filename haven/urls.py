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
    
    # Feature URLs
    path('journal/', views.journal_view, name='journal'),
    path('mood-check/', views.mood_check_view, name='mood_check'),
    path('study/', views.study_log_view, name='study'),
    path('study-with-me/', views.study_with_me_view, name='study_with_me'),
    path('booking/', views.booking_view, name='booking'),
    path('chat/', views.chat_view, name='chat'),
    path('relax/', views.relax, name='relax'),
    
    # API Endpoints
    path('api/chat/', views.chat_with_ai, name='chat_api'),
    
    # Homepage
    path('', views.home, name='home'),
]