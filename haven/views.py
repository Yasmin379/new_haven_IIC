import json
import uuid
import re
from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.conf import settings

# RAG and AI imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
import google.generativeai as genai

from .models import (
    UserProfile, SpecialistProfile, JournalEntry, CounselorBooking,
    StudyLog, MoodLog, ChatSession, ChatMessage, DailyMotivation
)


class GuardianProtocol:
    """Implements the Guardian Protocol for safe AI interactions"""
    
    # Emergency keywords that trigger crisis response
    EMERGENCY_KEYWORDS = [
        'suicide', 'kill myself', 'end my life', 'not worth living',
        'hurt myself', 'self harm', 'cut myself', 'overdose',
        'jump off', 'hang myself', 'shoot myself', 'die',
        'want to die', 'better off dead', 'no point living'
    ]
    
    # Crisis response message
    CRISIS_RESPONSE = """
    I'm really concerned about what you're sharing with me. Your safety is the most important thing right now.

    If you're having thoughts of hurting yourself, please reach out for help immediately:

    🇮🇳 **India Crisis Resources:**
    • KIRAN Mental Health Helpline: 1800-599-0019 (24/7, Toll-Free)
    • Vandrevala Foundation: 1860-266-2345 / +91-9999666555
    • iCALL: 9152987821 (Mon-Sat, 8 AM - 10 PM)
    • AASRA: 91-9820466726 (24/7)
    • Sneha India: 91-44-24640050 (24/7)
    
    🌍 **International Crisis Resources:**
    • National Suicide Prevention Lifeline: 988 (US)
    • Crisis Text Line: Text HOME to 741741 (US)
    • Emergency Services: 112 (India) / 911 (US)

    You are not alone, and there are people who want to help you. Please reach out to a trusted friend, family member, or mental health professional right now.

    Your life has value, and things can get better. Please stay safe. 🌟
    """
    
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        if not self.api_key or self.api_key == 'your_google_api_key_here':
            raise ValueError("Google API key not configured")
        
        genai.configure(api_key=self.api_key)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.api_key,
            temperature=0.7
        )
        
        # Initialize embeddings and vector store
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )
        
        self.vector_store = Chroma(
            persist_directory=str(settings.RAG_VECTOR_STORE_DIR),
            embedding_function=self.embeddings,
            collection_name="haven_knowledge_base"
        )
    
    def is_emergency(self, message: str) -> bool:
        """Check if message contains emergency keywords"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.EMERGENCY_KEYWORDS)
    
    def retrieve_context(self, query: str, k: int = 3) -> str:
        """Retrieve relevant context from knowledge base"""
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""
    
    def generate_response(self, user_message: str, context: str, user_profile: UserProfile) -> str:
        """Generate AI response using RAG"""
        system_prompt = f"""
        You are BUDDY, a warm, empathetic, and knowledgeable AI companion for the HAVEN mental health platform. 
        
        User's cheerful username: {user_profile.cheerful_username}
        
        Guidelines:
        - Be supportive, non-judgmental, and encouraging
        - Use the provided context to give accurate, helpful information
        - Keep responses conversational and warm
        - If you don't know something, say so and suggest consulting a professional
        - Never provide medical diagnoses or treatment recommendations
        - Encourage professional help when appropriate
        - Use emojis sparingly to add warmth
        
        Context from knowledge base:
        {context}
        
        Respond to the user's message with empathy and helpful information.
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm(messages)
            return response.content
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, I'm having trouble responding right now. Please try again later or reach out to a mental health professional if you need immediate support."
    
    def process_message(self, user_message: str, user_profile: UserProfile) -> dict:
        """Process user message through Guardian Protocol"""
        # Step 1: Safety Check
        if self.is_emergency(user_message):
            return {
                'response': self.CRISIS_RESPONSE,
                'is_emergency': True,
                'status': 'crisis_detected'
            }
        
        # Step 2: Retrieve Context
        context = self.retrieve_context(user_message)
        
        # Step 3: Generate Response
        response = self.generate_response(user_message, context, user_profile)
        
        return {
            'response': response,
            'is_emergency': False,
            'status': 'success'
        }


# --- Authentication Views ---

def login_view(request):
    """Handle user login with role-based redirection"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Role-based redirection
            if user.is_superuser:
                return redirect('/admin/')
            elif hasattr(user, 'specialistprofile'):
                return redirect('specialist_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'haven/login.html')


def signup_view(request):
    """Handle user registration with cheerful username generation"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        gender = request.POST.get('gender')
        user_role = request.POST.get('user_role')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            try:
                with transaction.atomic():
                    # Create user
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password1
                    )
                    
                    # Set admin status if role is admin
                    if user_role == 'admin':
                        user.is_superuser = True
                        user.is_staff = True
                        user.save()
                    
                    # Create user profile with cheerful username
                    profile = user.userprofile
                    profile.gender = gender
                    profile.save()
                    
                    # Create specialist profile if role is counselor
                    if user_role == 'counselor':
                        SpecialistProfile.objects.create(
                            user=user,
                            specialty='General Counseling',
                            available_times={},
                            bio='Welcome to HAVEN!',
                            experience_years=0,
                            is_verified=False
                        )
                    
                    messages.success(request, f'Account created successfully! Your cheerful username is: {profile.cheerful_username}')
                    return redirect('login')
                    
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'haven/signup.html')


def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('login')


# --- Dashboard Views ---

@login_required
def user_dashboard(request):
    """User dashboard with daily motivation and features"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get today's motivation
    today = date.today()
    try:
        motivation = DailyMotivation.objects.get(date=today, is_active=True)
    except DailyMotivation.DoesNotExist:
        motivation = DailyMotivation.objects.create(
            date=today,
            message="Every new day is a fresh start. You've got this! 🌟",
            is_active=True
        )
    
    # Get recent journal entries
    recent_entries = JournalEntry.objects.filter(user=request.user)[:5]
    
    # Get recent mood logs
    recent_mood_logs = MoodLog.objects.filter(user=request.user)[:3]
    
    context = {
        'profile': profile,
        'motivation': motivation,
        'recent_entries': recent_entries,
        'recent_mood_logs': recent_mood_logs,
    }
    
    return render(request, 'haven/user_dashboard.html', context)


@login_required
def specialist_dashboard(request):
    """Specialist dashboard for mental health professionals"""
    if not hasattr(request.user, 'specialistprofile'):
        messages.error(request, 'Access denied. This area is for specialists only.')
        return redirect('user_dashboard')
    
    specialist = request.user.specialistprofile
    
    # Get upcoming bookings (showing only anonymous usernames)
    upcoming_bookings = CounselorBooking.objects.filter(
        specialist=specialist,
        status__in=['pending', 'confirmed'],
        date__gte=date.today()
    ).order_by('date', 'time')
    
    # Get recent bookings
    recent_bookings = CounselorBooking.objects.filter(
        specialist=specialist
    ).order_by('-date', '-time')[:10]
    
    context = {
        'specialist': specialist,
        'upcoming_bookings': upcoming_bookings,
        'recent_bookings': recent_bookings,
    }
    
    return render(request, 'haven/specialist_dashboard.html', context)


# --- Feature Views ---

@login_required
def journal_view(request):
    """Journal page with book-like UI"""
    if request.method == 'POST':
        text = request.POST.get('text')
        mood_rating = request.POST.get('mood_rating')
        
        if text:
            JournalEntry.objects.create(
                user=request.user,
                text=text,
                mood_rating=mood_rating if mood_rating else None
            )
            messages.success(request, 'Journal entry saved successfully!')
            return redirect('journal')
    
    # Get all journal entries for the user
    entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'entries': entries,
    }
    
    return render(request, 'haven/journal.html', context)


@login_required
def mood_check_view(request):
    """PHQ-2 and GAD-2 mood check-in"""
    if request.method == 'POST':
        phq2_q1 = int(request.POST.get('phq2_q1', 0))
        phq2_q2 = int(request.POST.get('phq2_q2', 0))
        gad2_q1 = int(request.POST.get('gad2_q1', 0))
        gad2_q2 = int(request.POST.get('gad2_q2', 0))
        notes = request.POST.get('notes', '')
        
        mood_log = MoodLog.objects.create(
            user=request.user,
            phq2_question1=phq2_q1,
            phq2_question2=phq2_q2,
            gad2_question1=gad2_q1,
            gad2_question2=gad2_q2,
            notes=notes
        )
        
        # Provide feedback based on scores
        if mood_log.risk_level == 'high':
            messages.warning(request, 'Your responses suggest you might benefit from speaking with a mental health professional. Please consider reaching out for support.')
        elif mood_log.risk_level == 'moderate':
            messages.info(request, 'Thank you for checking in. Consider practicing self-care activities or speaking with someone you trust.')
        else:
            messages.success(request, 'Thank you for checking in. Keep up the great work with your mental health!')
        
        return redirect('user_dashboard')
    
    return render(request, 'haven/mood_check.html')


@login_required
def study_log_view(request):
    """Study time tracking with weekly totals and shoutouts"""
    if request.method == 'POST':
        duration = int(request.POST.get('duration', 0))
        subject = request.POST.get('subject', '')
        notes = request.POST.get('notes', '')
        
        StudyLog.objects.create(
            user=request.user,
            duration_minutes=duration,
            subject=subject,
            notes=notes
        )
        
        messages.success(request, 'Study session logged successfully!')
        return redirect('study')
    
    # Get recent study logs
    study_logs = StudyLog.objects.filter(user=request.user).order_by('-log_date', '-created_at')[:20]
    
    # Calculate weekly total
    from datetime import timedelta
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_logs = StudyLog.objects.filter(
        user=request.user,
        log_date__gte=week_start
    )
    total_minutes = sum(log.duration_minutes for log in week_logs)
    total_hours = round(total_minutes / 60, 1)
    
    # Motivational shoutout based on weekly total
    shoutout = None
    shoutout_icon = None
    if total_hours >= 15:
        shoutout = "Outstanding! You're a study champion with 15+ hours this week!"
        shoutout_icon = "🏆"
    elif total_hours >= 10:
        shoutout = "Amazing! You've studied 10+ hours this week! Keep it up!"
        shoutout_icon = "🌟"
    elif total_hours >= 5:
        shoutout = "Great work! You're building excellent study habits!"
        shoutout_icon = "💪"
    elif total_hours >= 1:
        shoutout = "Good start! Keep up the momentum!"
        shoutout_icon = "🎯"
    
    context = {
        'study_logs': study_logs,
        'total_hours_week': total_hours,
        'total_minutes_week': total_minutes,
        'shoutout': shoutout,
        'shoutout_icon': shoutout_icon,
    }
    
    return render(request, 'haven/study.html', context)


@login_required
def booking_view(request):
    """Counselor booking system"""
    specialists = SpecialistProfile.objects.filter(is_verified=True)
    
    if request.method == 'POST':
        specialist_id = request.POST.get('specialist')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        concern = request.POST.get('concern')
        
        if specialist_id and date_str and time_str and concern:
            specialist = get_object_or_404(SpecialistProfile, id=specialist_id)
            profile = request.user.profile
            
            booking = CounselorBooking.objects.create(
                client_username=profile.cheerful_username,
                specialist=specialist,
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                time=datetime.strptime(time_str, '%H:%M').time(),
                concern=concern
            )
            
            messages.success(request, f'Booking request sent to {specialist.user.get_full_name()}. You will be contacted soon.')
            return redirect('booking')
    
    context = {
        'specialists': specialists,
    }
    
    return render(request, 'haven/booking.html', context)


@login_required
def chat_view(request):
    """Chat interface with BUDDY"""
    # Get or create active chat session
    session, created = ChatSession.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'session_id': str(uuid.uuid4())}
    )
    
    # Get recent messages
    messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
    
    context = {
        'session': session,
        'messages': messages,
    }
    
    return render(request, 'haven/chat.html', context)


# --- API Endpoints ---

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def chat_with_ai(request):
    """Guardian Protocol chat API endpoint"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'response': 'Please enter a message.',
                'status': 'error'
            })
        
        # Get user profile
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return JsonResponse({
                'response': 'User profile not found. Please contact support.',
                'status': 'error'
            })
        
        # Initialize Guardian Protocol
        guardian = GuardianProtocol()
        
        # Process message through Guardian Protocol
        result = guardian.process_message(user_message, profile)
        
        # Get or create chat session
        session, created = ChatSession.objects.get_or_create(
            user=request.user,
            is_active=True,
            defaults={'session_id': str(uuid.uuid4())}
        )
        
        # Save user message
        ChatMessage.objects.create(
            session=session,
            message_type='user',
            content=user_message,
            is_emergency=result['is_emergency']
        )
        
        # Save AI response
        ChatMessage.objects.create(
            session=session,
            message_type='ai',
            content=result['response'],
            is_emergency=result['is_emergency']
        )
        
        return JsonResponse({
            'response': result['response'],
            'status': result['status'],
            'is_emergency': result['is_emergency']
        })
        
    except Exception as e:
        return JsonResponse({
            'response': 'I apologize, but I\'m experiencing technical difficulties. Please try again later or reach out to a mental health professional if you need immediate support.',
            'status': 'error',
            'is_emergency': False
        })


# --- General Page Views ---

def home(request):
    """Homepage - redirect to login or appropriate dashboard"""
    if request.user.is_authenticated:
        # Redirect authenticated users to their appropriate dashboard
        if request.user.is_superuser:
            return redirect('/admin/')
        elif hasattr(request.user, 'specialistprofile'):
            return redirect('specialist_dashboard')
        else:
            return redirect('user_dashboard')
    else:
        # Redirect unauthenticated users to login
        return redirect('login')


@login_required
def relax(request):
    """Relaxation and mindfulness page with YouTube content"""
    from .models import MediaPlaylist
    
    # Get all relax content by type
    breathing = MediaPlaylist.objects.filter(
        category='RELAX',
        content_type='BREATHING',
        is_active=True
    ).order_by('order')
    
    yoga = MediaPlaylist.objects.filter(
        category='RELAX',
        content_type='YOGA',
        is_active=True
    ).order_by('order')
    
    asmr = MediaPlaylist.objects.filter(
        category='RELAX',
        content_type='ASMR',
        is_active=True
    ).order_by('order')
    
    chill_music = MediaPlaylist.objects.filter(
        category='RELAX',
        content_type='CHILL_MUSIC',
        is_active=True
    ).order_by('order')
    
    context = {
        'breathing_sessions': breathing,
        'yoga_sessions': yoga,
        'asmr_videos': asmr,
        'chill_music': chill_music,
    }
    
    return render(request, 'haven/relax.html', context)


@login_required
def study_with_me_view(request):
    """Study With Me page with music, tips, Pomodoro timer, and motivational content"""
    from .models import MediaPlaylist
    
    # Get all study-related content
    study_music = MediaPlaylist.objects.filter(
        category='STUDY',
        content_type='STUDY_MUSIC',
        is_active=True
    ).order_by('order')
    
    study_tips = MediaPlaylist.objects.filter(
        category='STUDY',
        content_type='STUDY_TIPS',
        is_active=True
    ).order_by('order')
    
    motivation = MediaPlaylist.objects.filter(
        category='STUDY',
        content_type='MOTIVATION',
        is_active=True
    ).order_by('order')
    
    context = {
        'study_music': study_music,
        'study_tips': study_tips,
        'motivation_videos': motivation,
    }
    
    return render(request, 'haven/study_with_me.html', context)