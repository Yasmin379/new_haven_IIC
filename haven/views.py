import json
from multiprocessing import context
from unittest import result
from urllib import response
import uuid
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
from opentelemetry import context
import requests

from .rag_engine import retrieve, build_prompt

from .models import (
    UserProfile, SpecialistProfile, JournalEntry, CounselorBooking,
    StudyLog, MoodLog, ChatSession, ChatMessage, DailyMotivation
)

OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "phi3:mini"


class GuardianProtocol:
    EMERGENCY_KEYWORDS = [
        'suicide', 'kill myself', 'end my life', 'not worth living',
        'hurt myself', 'self harm', 'cut myself', 'overdose',
        'jump off', 'hang myself', 'want to die', 'better off dead',
        'no point living', 'end it all', 'cannot go on', 'no reason to live'
    ]

    CRISIS_RESPONSE = """
I'm really concerned about what you're sharing with me. Your safety is the most important thing right now.

If you're having thoughts of hurting yourself, please reach out for help immediately:

🇮🇳 **India Crisis Resources:**
• KIRAN Mental Health Helpline: 1800-599-0019 (24/7, Toll-Free)
• Vandrevala Foundation: 1860-266-2345
• iCALL: 9152987821 (Mon-Sat, 8 AM - 10 PM)
• AASRA: 91-9820466627 (24/7)
• Emergency Services: 112

You are not alone. Please reach out to a trusted friend, family member, or mental health professional right now.
Your life has value, and things can get better. Please stay safe. 🌟
"""

    def is_emergency(self, message):
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.EMERGENCY_KEYWORDS)

    def _call_ollama(self, user_message, context):
        clean_prompt = f"""You are BUDDY, a caring friend talking to a stressed college student in India.
    Context: {context[:100] if context else ''}
    Student said: "{user_message}"
    BUDDY replies warmly in 1-2 sentences (no greetings, no lists, no "[Name]"):"""

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": clean_prompt,
            "stream": False,
            "options": {
                "num_predict": 100,
                "temperature": 0.8,
                "num_ctx": 512,
                "stop": ["\n", "Student:", "BUDDY:"]
                
            }
            }
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=300
        )
        response.raise_for_status()
        result = response.json().get("response", "").strip()
        # Clean up any leftover artifacts
        print(f"[OLLAMA OUTPUT] '{result}'")  # ADD THIS
        result = result.replace("[Name]", "").replace("Greetings,", "").strip()
        return result if result else "I hear you, and I'm here for you! 😊 Want to tell me more about what's going on?"
    def generate_response(self, user_message, context, user_profile):
        try:
            return self._call_ollama(user_message, context)
        except Exception as e:
            print(f"[HAVEN BUDDY Error] {e}")
            return "Hey, I'm here for you! 😊 Try sharing a bit more about what's on your mind."
    

    def process_message(self, user_message, user_profile):
        if self.is_emergency(user_message):
            return {
                'response': self.CRISIS_RESPONSE,
                'is_emergency': True,
                'status': 'crisis_detected'
            }
        retrieved_chunks = retrieve(user_message)
        context = "\n\n".join(retrieved_chunks) if retrieved_chunks else "Provide general mental health support."
        response = self.generate_response(user_message, context, user_profile)
        return {
            'response': response,
            'is_emergency': False,
            'status': 'success'
        }


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
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
                    user = User.objects.create_user(username=username, email=email, password=password1)
                    if user_role == 'admin':
                        user.is_superuser = True
                        user.is_staff = True
                        user.save()
                    profile = user.userprofile
                    profile.gender = gender
                    profile.save()
                    if user_role == 'counselor':
                        SpecialistProfile.objects.create(
                            user=user, specialty='General Counseling',
                            available_times={}, bio='Welcome to HAVEN!',
                            experience_years=0, is_verified=False
                        )
                    messages.success(request, f'Account created! Your cheerful username is: {profile.cheerful_username}')
                    return redirect('login')
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
    return render(request, 'haven/signup.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def user_dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.user.first_name or request.user.last_name:
        user_display_name = f"{request.user.first_name} {request.user.last_name}".strip()
    else:
        user_display_name = request.user.username
    today = date.today()
    try:
        motivation = DailyMotivation.objects.get(date=today, is_active=True)
    except DailyMotivation.DoesNotExist:
        motivation = DailyMotivation.objects.create(
            date=today,
            message="Every new day is a fresh start. You've got this! 🌟",
            is_active=True
        )
    recent_entries = JournalEntry.objects.filter(user=request.user)[:5]
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
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        profile.gender = request.POST.get('gender', '')
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')
    full_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    context = {
        'profile': profile,
        'full_name': full_name,
        'account_created': request.user.date_joined,
        'user': request.user,
    }
    return render(request, 'haven/profile.html', context)


@login_required
def specialist_dashboard(request):
    if not hasattr(request.user, 'specialistprofile'):
        messages.error(request, 'Access denied. This area is for specialists only.')
        return redirect('user_dashboard')
    specialist = request.user.specialistprofile
    upcoming_bookings = CounselorBooking.objects.filter(
        specialist=specialist, status__in=['pending', 'confirmed'], date__gte=date.today()
    ).order_by('date', 'time')
    recent_bookings = CounselorBooking.objects.filter(specialist=specialist).order_by('-date', '-time')[:10]
    context = {
        'specialist': specialist,
        'upcoming_bookings': upcoming_bookings,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'haven/specialist_dashboard.html', context)


@login_required
def journal_view(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        mood_rating = request.POST.get('mood_rating')
        if text:
            JournalEntry.objects.create(
                user=request.user, text=text,
                mood_rating=mood_rating if mood_rating else None
            )
            messages.success(request, 'Journal entry saved successfully!')
            return redirect('journal')
    entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'haven/journal.html', {'entries': entries})


@login_required
def journal_detail(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        mood_map = {1: '😢', 2: '😕', 3: '😐', 4: '🙂', 5: '😄'}
        return JsonResponse({
            'id': entry.id, 'text': entry.text,
            'mood_rating': entry.mood_rating,
            'mood_emoji': mood_map.get(entry.mood_rating, ''),
            'created_at': entry.created_at.strftime('%B %d, %Y at %I:%M %p'),
        })
    entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'haven/journal.html', {'entries': entries, 'open_entry': entry})


@login_required
def mood_check_view(request):
    if request.method == 'POST':
        phq2_q1 = int(request.POST.get('phq2_q1', 0))
        phq2_q2 = int(request.POST.get('phq2_q2', 0))
        gad2_q1 = int(request.POST.get('gad2_q1', 0))
        gad2_q2 = int(request.POST.get('gad2_q2', 0))
        notes = request.POST.get('notes', '')
        mood_log = MoodLog.objects.create(
            user=request.user, phq2_question1=phq2_q1, phq2_question2=phq2_q2,
            gad2_question1=gad2_q1, gad2_question2=gad2_q2, notes=notes
        )
        if mood_log.risk_level == 'high':
            messages.warning(request, 'Your responses suggest you might benefit from speaking with a mental health professional.')
        elif mood_log.risk_level == 'moderate':
            messages.info(request, 'Thank you for checking in. Consider practicing self-care or speaking with someone you trust.')
        else:
            messages.success(request, 'Thank you for checking in. Keep up the great work!')
        return redirect('user_dashboard')
    return render(request, 'haven/mood_check.html')


@login_required
def study_log_view(request):
    if request.method == 'POST':
        duration = int(request.POST.get('duration', 0))
        subject = request.POST.get('subject', '')
        notes = request.POST.get('notes', '')
        StudyLog.objects.create(user=request.user, duration_minutes=duration, subject=subject, notes=notes)
        messages.success(request, 'Study session logged successfully!')
        return redirect('study')
    study_logs = StudyLog.objects.filter(user=request.user).order_by('-log_date', '-created_at')[:20]
    from datetime import timedelta
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_logs = StudyLog.objects.filter(user=request.user, log_date__gte=week_start)
    total_minutes = sum(log.duration_minutes for log in week_logs)
    total_hours = round(total_minutes / 60, 1)
    shoutout = shoutout_icon = None
    if total_hours >= 15:
        shoutout, shoutout_icon = "Outstanding! You're a study champion with 15+ hours this week!", "🏆"
    elif total_hours >= 10:
        shoutout, shoutout_icon = "Amazing! You've studied 10+ hours this week!", "🌟"
    elif total_hours >= 5:
        shoutout, shoutout_icon = "Great work! You're building excellent study habits!", "💪"
    elif total_hours >= 1:
        shoutout, shoutout_icon = "Good start! Keep up the momentum!", "🎯"
    context = {
        'study_logs': study_logs, 'total_hours_week': total_hours,
        'total_minutes_week': total_minutes, 'shoutout': shoutout, 'shoutout_icon': shoutout_icon,
    }
    return render(request, 'haven/study.html', context)


@login_required
def booking_view(request):
    specialists = SpecialistProfile.objects.filter(is_verified=True)
    if request.method == 'POST':
        specialist_id = request.POST.get('specialist')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        concern = request.POST.get('concern')
        if specialist_id and date_str and time_str and concern:
            specialist = get_object_or_404(SpecialistProfile, id=specialist_id)
            profile = request.user.userprofile
            CounselorBooking.objects.create(
                client_username=profile.cheerful_username, specialist=specialist,
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                time=datetime.strptime(time_str, '%H:%M').time(), concern=concern
            )
            messages.success(request, f'Booking request sent to {specialist.user.get_full_name()}. You will be contacted soon.')
            return redirect('booking')
    return render(request, 'haven/booking.html', {'specialists': specialists})


@login_required
def chat_view(request):
    session, created = ChatSession.objects.get_or_create(
        user=request.user, is_active=True,
        defaults={'session_id': str(uuid.uuid4())}
    )
    chat_messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
    return render(request, 'haven/chat.html', {'session': session, 'messages': chat_messages})


@csrf_exempt
@require_http_methods(["POST"])
def chat_with_ai(request):
    """Guardian Protocol chat API — RAG + local Ollama, zero data leaves machine"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        if not user_message:
            return JsonResponse({'response': 'Please enter a message.', 'status': 'error'})

        try:
            profile = request.user.userprofile
        except Exception:
            return JsonResponse({'response': 'User profile not found.', 'status': 'error'})

        guardian = GuardianProtocol()
        result = guardian.process_message(user_message, profile)

        session, _ = ChatSession.objects.get_or_create(
            user=request.user, is_active=True,
            defaults={'session_id': str(uuid.uuid4())}
        )
        ChatMessage.objects.create(session=session, message_type='user', content=user_message, is_emergency=result['is_emergency'])
        ChatMessage.objects.create(session=session, message_type='ai', content=result['response'], is_emergency=result['is_emergency'])

        return JsonResponse({
            'response': result['response'],
            'status': result['status'],
            'is_emergency': result['is_emergency']
        })

    except Exception as e:
        print(f"[HAVEN Chat Error] {e}")
        return JsonResponse({
            'response': "I'm here for you. Please try again in a moment.",
            'status': 'error',
            'is_emergency': False
        })


def home(request):
    return landing(request)


def landing(request):
    return render(request, 'haven/landing.html')


@login_required
def relax(request):
    from .models import MediaPlaylist
    breathing = MediaPlaylist.objects.filter(category='RELAX', content_type='BREATHING', is_active=True).order_by('order')
    yoga = MediaPlaylist.objects.filter(category='RELAX', content_type='YOGA', is_active=True).order_by('order')
    asmr = MediaPlaylist.objects.filter(category='RELAX', content_type='ASMR', is_active=True).order_by('order')
    chill_music = MediaPlaylist.objects.filter(category='RELAX', content_type='CHILL_MUSIC', is_active=True).order_by('order')
    context = {
        'breathing_sessions': breathing, 'yoga_sessions': yoga,
        'asmr_videos': asmr, 'chill_music': chill_music,
    }
    return render(request, 'haven/relax.html', context)


@login_required
def study_with_me_view(request):
    from .models import MediaPlaylist, StudyBackgroundMusic, StudyVideo
    music_tracks = StudyBackgroundMusic.objects.filter(is_active=True).order_by('order', 'title')
    study_videos = StudyVideo.objects.filter(category='tips', is_active=True).order_by('order', 'title')
    motivational_videos = StudyVideo.objects.filter(category='motivation', is_active=True).order_by('order', 'title')
    legacy_study_music = MediaPlaylist.objects.filter(category='STUDY', content_type='STUDY_MUSIC', is_active=True).order_by('order')
    context = {
        'music_tracks': music_tracks, 'legacy_study_music': legacy_study_music,
        'study_videos': study_videos, 'motivational_videos': motivational_videos,
    }
    return render(request, 'haven/study_with_me.html', context)