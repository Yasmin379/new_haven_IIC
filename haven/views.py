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
from django.db import transaction, models
from django.conf import settings
from django.shortcuts import render

# RAG and AI imports
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_chroma import Chroma
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_core.messages import HumanMessage, SystemMessage
# import google.generativeai as genai

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

# ── Role-based access decorators ──────────────────────────────────────────────

def student_required(view_func):
    """Redirect counselors away from student-only pages."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'specialistprofile'):
            messages.warning(request, 'That page is for students only.')
            return redirect('specialist_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def counselor_required(view_func):
    """Redirect students away from counselor-only pages."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and not hasattr(request.user, 'specialistprofile'):
            messages.warning(request, 'That page is for counselors only.')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

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
@student_required
def user_dashboard(request):
    """User dashboard with daily motivation and features"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's display name (first name + last name, or username as fallback)
    if request.user.first_name or request.user.last_name:
        user_display_name = f"{request.user.first_name} {request.user.last_name}".strip()
    else:
        user_display_name = request.user.username
    
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
        'user_display_name': user_display_name,
        'motivation': motivation,
        'recent_entries': recent_entries,
        'recent_mood_logs': recent_mood_logs,
    }
    
    return render(request, 'haven/user_dashboard.html', context)


@login_required
def user_profile(request):
    """User profile page showing account details"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user information
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # Update profile
        profile.gender = request.POST.get('gender', '')
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')
    
    # Get user's full name
    full_name = ""
    if request.user.first_name or request.user.last_name:
        full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    else:
        full_name = request.user.username
    
    # Get account creation date
    account_created = request.user.date_joined
    
    context = {
        'profile': profile,
        'full_name': full_name,
        'account_created': account_created,
        'user': request.user,
    }
    
    return render(request, 'haven/profile.html', context)


@login_required
@counselor_required
def specialist_dashboard(request):
    """Specialist dashboard for mental health professionals"""
    if not hasattr(request.user, 'specialistprofile'):
        messages.error(request, 'Access denied. This area is for specialists only.')
        return redirect('user_dashboard')

    specialist = request.user.specialistprofile

    # Counselor's display name — username, no hardcoded prefix
    counselor_name = request.user.username

    now = timezone.now()
    today = now.date()
    now_time = now.time()

    # Upcoming: confirmed/accepted bookings in the future
    upcoming_sessions = (
        CounselorBooking.objects
        .filter(specialist=specialist, status__in=['confirmed', 'accepted'])
        .filter(
            models.Q(date__gt=today) |
            models.Q(date=today, time__gte=now_time)
        )
        .order_by('date', 'time')
    )

    # History: all bookings whose date+time is in the past
    session_history = (
        CounselorBooking.objects
        .filter(specialist=specialist)
        .filter(
            models.Q(date__lt=today) |
            models.Q(date=today, time__lt=now_time)
        )
        .order_by('-date', '-time')[:20]
    )

    # Pending requests (for the live booking-requests panel)
    pending_bookings = CounselorBooking.objects.filter(
        specialist=specialist,
        status='pending',
    ).order_by('date', 'time')

    context = {
        'specialist':        specialist,
        'counselor_name':    counselor_name,
        'upcoming_sessions': upcoming_sessions,
        'session_history':   session_history,
        'pending_bookings':  pending_bookings,
    }

    return render(request, 'haven/specialist_dashboard.html', context)


@login_required
def api_my_sessions(request):
    """
    JSON API for students — returns all their bookings with current status.
    Polled every 15 s so the student sees counselor acceptance in real time.
    """
    bookings = (
        CounselorBooking.objects
        .filter(student=request.user)
        .select_related('specialist__user')
        .order_by('-date', '-time')
    )

    data = []
    for b in bookings:
        sp   = b.specialist
        name = sp.user.get_full_name().strip()
        data.append({
            'id':             b.id,
            'counselor_name': name if name else sp.user.username,
            'specialty':      sp.get_specialty_display(),
            'date':           b.date.strftime('%Y-%m-%d'),
            'time':           b.time.strftime('%H:%M'),
            'session_time':   f"{b.date.strftime('%Y-%m-%d')}T{b.time.strftime('%H:%M:%S')}",
            'status':         b.status,
            'concern':        b.concern[:100] + '…' if len(b.concern) > 100 else b.concern,
            'notes':          b.notes,
        })

    return JsonResponse({'bookings': data})


@login_required
def api_booking_requests(request):
    """
    JSON API — returns all booking requests for the logged-in counselor.
    Polled by the specialist dashboard every 15 seconds for real-time updates.
    Only requests addressed to THIS counselor are returned.
    """
    if not hasattr(request.user, 'specialistprofile'):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    specialist = request.user.specialistprofile

    bookings = (
        CounselorBooking.objects
        .filter(specialist=specialist)
        .order_by('-date', '-time')
    )

    requests_data = []
    for b in bookings:
        requests_data.append({
            'id':           b.id,
            'student_name': b.client_username,   # anonymous cheerful username
            'date':         b.date.strftime('%Y-%m-%d'),
            'time':         b.time.strftime('%H:%M'),
            'session_time': f"{b.date.strftime('%Y-%m-%d')}T{b.time.strftime('%H:%M:%S')}",
            'concern':      b.concern[:120] + '…' if len(b.concern) > 120 else b.concern,
            'status':       b.status,
        })

    return JsonResponse({
        'requests':         requests_data,
        'pending_count':    sum(1 for r in requests_data if r['status'] == 'pending'),
        'confirmed_count':  sum(1 for r in requests_data if r['status'] == 'confirmed'),
        'total_count':      len(requests_data),
    })


@login_required
def api_sessions_data(request):
    """
    JSON API — returns upcoming sessions and session history for the logged-in counselor.
    Called by the specialist dashboard JS to populate the two toggle sections.
    """
    if not hasattr(request.user, 'specialistprofile'):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    specialist = request.user.specialistprofile
    now        = timezone.now()
    today      = now.date()
    now_time   = now.time()

    # Upcoming: confirmed/accepted, date+time in the future
    upcoming_qs = (
        CounselorBooking.objects
        .filter(specialist=specialist, status__in=['confirmed', 'accepted'])
        .filter(
            models.Q(date__gt=today) |
            models.Q(date=today, time__gte=now_time)
        )
        .order_by('date', 'time')
    )

    # History: any booking whose date+time is in the past
    history_qs = (
        CounselorBooking.objects
        .filter(specialist=specialist)
        .filter(
            models.Q(date__lt=today) |
            models.Q(date=today, time__lt=now_time)
        )
        .order_by('-date', '-time')[:50]
    )

    def serialize(b):
        return {
            'student_name': b.client_username,
            'date':         b.date.strftime('%Y-%m-%d'),
            'time':         b.time.strftime('%H:%M'),
            'session_time': f"{b.date.strftime('%Y-%m-%d')}T{b.time.strftime('%H:%M:%S')}",
            'status':       b.status,
            'notes':        b.notes or '',
        }

    return JsonResponse({
        'counselor_name':    request.user.username,
        'upcoming_sessions': [serialize(b) for b in upcoming_qs],
        'history_sessions':  [serialize(b) for b in history_qs],
    })


@require_http_methods(["POST"])
@login_required
def api_update_booking_status(request, booking_id):
    """
    JSON API — counselor accepts or declines a booking request.
    POST body: { "status": "confirmed" | "cancelled" }
    Only the counselor the booking belongs to can update it.
    """
    if not hasattr(request.user, 'specialistprofile'):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    specialist = request.user.specialistprofile
    booking    = get_object_or_404(CounselorBooking, id=booking_id, specialist=specialist)

    try:
        data       = json.loads(request.body)
        new_status = data.get('status', '').strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    allowed = {'confirmed', 'cancelled', 'completed', 'pending'}
    if new_status not in allowed:
        return JsonResponse({'error': f'Invalid status. Allowed: {allowed}'}, status=400)

    booking.status = new_status
    booking.save(update_fields=['status'])

    return JsonResponse({
        'success':    True,
        'booking_id': booking.id,
        'new_status': booking.status,
    })


# --- Feature Views ---

@login_required
@student_required
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
def journal_detail(request, entry_id):
    """View a single journal entry — returns JSON for AJAX or full page"""
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    # AJAX request from the modal
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        mood_map = {1: '😢', 2: '😕', 3: '😐', 4: '🙂', 5: '😄'}
        return JsonResponse({
            'id': entry.id,
            'text': entry.text,
            'mood_rating': entry.mood_rating,
            'mood_emoji': mood_map.get(entry.mood_rating, ''),
            'created_at': entry.created_at.strftime('%B %d, %Y at %I:%M %p'),
        })
    
    # Non-AJAX: render full page (fallback)
    entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'haven/journal.html', {
        'entries': entries,
        'open_entry': entry,
    })


@require_http_methods(["DELETE"])
@login_required
def journal_delete(request, entry_id):
    """Delete a journal entry — only the owner can delete their own entry."""
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    entry.delete()
    return JsonResponse({'success': True, 'deleted_id': entry_id})


@login_required
@student_required
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
@student_required
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
def get_counselors(request):
    """
    API endpoint — returns all active counselors for the booking dropdown.
    A counselor is 'active' if they have a SpecialistProfile and their
    Django user account is active (is_active=True).
    The list updates in real time: add/remove a SpecialistProfile in admin
    and the next dropdown fetch reflects it immediately.
    """
    counselors = (
        SpecialistProfile.objects
        .filter(user__is_active=True)          # only active user accounts
        .select_related('user')                # single JOIN, no N+1
        .order_by('user__first_name', 'user__last_name')
    )

    data = []
    for sp in counselors:
        full_name = sp.user.get_full_name().strip()
        # Fall back to username if no name is set
        display_name = full_name if full_name else sp.user.username
        data.append({
            "id":        sp.id,
            "name":      display_name,
            "specialty": sp.get_specialty_display(),
            "verified":  sp.is_verified,
        })

    return JsonResponse({"counselors": data})


@login_required
@student_required
def booking_view(request):
    """Counselor booking system"""
    # Show all counselors with active accounts — verified badge shown in template
    specialists = (
        SpecialistProfile.objects
        .filter(user__is_active=True)
        .select_related('user')
        .order_by('user__first_name', 'user__last_name')
    )
    
    if request.method == 'POST':
        specialist_id = request.POST.get('specialist')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        concern = request.POST.get('concern')
        
        if specialist_id and date_str and time_str and concern:
            specialist = get_object_or_404(SpecialistProfile, id=specialist_id)

            # get_or_create is safe for users who existed before the signal was added
            profile, _ = UserProfile.objects.get_or_create(user=request.user)

            booking = CounselorBooking.objects.create(
                student=request.user,                  # FK — enables student dashboard queries
                client_username=profile.cheerful_username,
                specialist=specialist,
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                time=datetime.strptime(time_str, '%H:%M').time(),
                concern=concern
            )
            
            messages.success(request, f'Booking request sent to {specialist.user.get_full_name()}. You will be contacted soon.')
            return redirect('booking')

    # Student's own bookings for the sidebar
    user_bookings = CounselorBooking.objects.filter(
        student=request.user
    ).select_related('specialist__user').order_by('-date', '-time')

    context = {
        'specialists':  specialists,
        'user_bookings': user_bookings,
    }

    return render(request, 'haven/booking.html', context)


@login_required
@student_required
def chat_view(request):
    """Chat interface — always opens a clean, empty session."""
    # Archive any existing active sessions so they appear in history
    ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)

    # Create a brand-new session every visit
    ChatSession.objects.create(
        user=request.user,
        session_id=str(uuid.uuid4()),
        is_active=True,
    )

    # No messages passed — the template starts empty
    return render(request, 'haven/chat.html')


@login_required
@student_required
def chat_history_api(request):
    """Return past (inactive) sessions with their messages as JSON."""
    past_sessions = (
        ChatSession.objects
        .filter(user=request.user, is_active=False)
        .order_by('-started_at')[:20]
    )

    history = []
    for s in past_sessions:
        msgs = list(
            ChatMessage.objects
            .filter(session=s)
            .order_by('timestamp')
            .values('message_type', 'content', 'timestamp', 'is_emergency')
        )
        if not msgs:
            continue
        history.append({
            'session_id': s.session_id,
            'started_at': s.started_at.strftime('%b %d, %Y  %I:%M %p'),
            'messages': [
                {
                    'type': m['message_type'],
                    'content': m['content'],
                    'time': m['timestamp'].strftime('%I:%M %p'),
                    'is_emergency': m['is_emergency'],
                }
                for m in msgs
            ],
        })

    return JsonResponse({'history': history})


# --- API Endpoints ---

@require_http_methods(["POST"])
@login_required
def chat_with_ai(request):
    """
    Chat API endpoint — backed by local Ollama LLM (mistral).

    Accepts:  POST /api/chat/  { "message": "..." }
    Returns:  { "response": "...", "status": "...", "is_emergency": bool }

    The response shape is identical to the previous Guardian Protocol
    implementation so the existing frontend requires zero changes.
    """
    from .services import ask_ollama
    from .utils import FALLBACK_RESPONSE

    try:
        # ── Parse request ──────────────────────────────────────────────────
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse(
                {"response": "Invalid request format.", "status": "error", "is_emergency": False},
                status=400,
            )

        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse(
                {"response": "Please enter a message.", "status": "error", "is_emergency": False},
                status=400,
            )

        # ── Call Ollama service (crisis detection happens inside) ──────────
        result = ask_ollama(user_message, request.session)

        # ── Persist to DB (same as before) ─────────────────────────────────
        try:
            chat_session, _ = ChatSession.objects.get_or_create(
                user=request.user,
                is_active=True,
                defaults={"session_id": str(uuid.uuid4())},
            )
            ChatMessage.objects.create(
                session=chat_session,
                message_type="user",
                content=user_message,
                is_emergency=result["is_emergency"],
            )
            ChatMessage.objects.create(
                session=chat_session,
                message_type="ai",
                content=result["response"],
                is_emergency=result["is_emergency"],
            )
        except Exception as db_err:
            # DB failure should not break the chat response
            import logging
            logging.getLogger("haven").warning("DB save failed: %s", db_err)

        return JsonResponse(result)

    except Exception as exc:
        import logging
        logging.getLogger("haven").exception("Unexpected error in chat_with_ai: %s", exc)
        return JsonResponse(
            {
                "response":     FALLBACK_RESPONSE,
                "status":       "error",
                "is_emergency": False,
            }
        )


@require_http_methods(["GET"])
@login_required
def chat_history_api(request):
    """
    API endpoint to retrieve chat history for the logged-in user.
    Returns past chat sessions (excluding the current active one).
    """
    try:
        # Get the current active session to exclude it
        active_session = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        # Get all past sessions (inactive ones), ordered by most recent first
        past_sessions = ChatSession.objects.filter(
            user=request.user,
            is_active=False
        ).order_by('-started_at')

        history = []
        for session in past_sessions:
            # Get messages for this session
            messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
            
            # Format messages for frontend
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    'type': msg.message_type,  # 'user' or 'ai'
                    'content': msg.content
                })
            
            # Only include sessions that have messages
            if formatted_messages:
                history.append({
                    'started_at': session.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'messages': formatted_messages
                })

        return JsonResponse({'history': history})

    except Exception as exc:
        import logging
        logging.getLogger("haven").exception("Error in chat_history_api: %s", exc)
        return JsonResponse({'history': [], 'error': 'Failed to load history'}, status=500)


# --- General Page Views ---

def home(request):
    """Kept for backward compatibility — delegates to landing"""
    return landing(request)


def landing(request):
    """Landing page — always shown, even to logged-in users"""
    return render(request, 'haven/landing.html')


@login_required
@student_required
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
@student_required
def study_with_me_view(request):
    """Study With Me page — music, study tips, motivational videos, Pomodoro"""
    from .models import MediaPlaylist, StudyBackgroundMusic, StudyVideo

    # ── Background music: StudyBackgroundMusic model, is_active=True ──
    # Admin path: Haven > Background Music Tracks
    music_tracks = StudyBackgroundMusic.objects.filter(
        is_active=True
    ).order_by('order', 'title')

    # ── Study tips: StudyVideo model, category='tips' ──
    # Admin path: Haven > Study Videos (set Category = Study Tips)
    study_videos = StudyVideo.objects.filter(
        category='tips',
        is_active=True
    ).order_by('order', 'title')

    # ── Motivational videos: StudyVideo model, category='motivation' ──
    # Admin path: Haven > Study Videos (set Category = Motivational)
    motivational_videos = StudyVideo.objects.filter(
        category='motivation',
        is_active=True
    ).order_by('order', 'title')

    # Legacy MediaPlaylist fallback (only used if no StudyVideo entries exist)
    legacy_study_music = MediaPlaylist.objects.filter(
        category='STUDY', content_type='STUDY_MUSIC', is_active=True
    ).order_by('order')

    context = {
        # Music tab
        'music_tracks':       music_tracks,
        'legacy_study_music': legacy_study_music,
        # Study tips tab
        'study_videos':       study_videos,
        # Motivation tab
        'motivational_videos': motivational_videos,
    }

    return render(request, 'haven/study_with_me.html', context)

