from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
import random
import string


class UserProfile(models.Model):
    """Extended user profile with cheerful username generation"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cheerful_username = models.CharField(max_length=50, unique=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.cheerful_username:
            self.cheerful_username = self.generate_cheerful_username()
        super().save(*args, **kwargs)
    
    def generate_cheerful_username(self):
        """Generate a short, catchy, cheerful username"""
        # Short, punchy positive words
        positive_words = [
            'Joy', 'Calm', 'Hope', 'Zen', 'Bright', 'Smile', 'Glow',
            'Happy', 'Peace', 'Light', 'Bliss', 'Grace', 'Kind', 'Pure',
            'Sunny', 'Warm', 'Cozy', 'Cool', 'Bold', 'Brave', 'Swift'
        ]
        
        # Short nature/cute words
        nature_words = [
            'Star', 'Moon', 'Sky', 'Sun', 'Wave', 'Cloud', 'Rose',
            'Fox', 'Bear', 'Wolf', 'Deer', 'Dove', 'Owl', 'Bee',
            'Leaf', 'Rain', 'Snow', 'Fire', 'Wind', 'Lake', 'Sea'
        ]
        
        # Random choice between different formats for variety
        format_choice = random.randint(1, 3)
        
        if format_choice == 1:
            # Format: PositiveNature (e.g., JoyStar, CalmMoon)
            first = random.choice(positive_words)
            second = random.choice(nature_words)
            username = f"{first}{second}"
        elif format_choice == 2:
            # Format: Positive + 2-digit number (e.g., Joy42, Calm88)
            word = random.choice(positive_words + nature_words)
            num = random.randint(10, 99)
            username = f"{word}{num}"
        else:
            # Format: NaturePositive (e.g., StarJoy, MoonCalm)
            first = random.choice(nature_words)
            second = random.choice(positive_words)
            username = f"{first}{second}"
        
        # Ensure uniqueness
        while UserProfile.objects.filter(cheerful_username=username).exists():
            # Regenerate if exists
            format_choice = random.randint(1, 3)
            if format_choice == 1:
                username = f"{random.choice(positive_words)}{random.choice(nature_words)}"
            elif format_choice == 2:
                username = f"{random.choice(positive_words + nature_words)}{random.randint(10, 99)}"
            else:
                username = f"{random.choice(nature_words)}{random.choice(positive_words)}"
        
        return username
    
    def __str__(self):
        return f"{self.cheerful_username} ({self.user.email})"


class SpecialistProfile(models.Model):
    """Profile for mental health specialists"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialty = models.CharField(max_length=100, choices=[
        ('psychologist', 'Psychologist'),
        ('psychiatrist', 'Psychiatrist'),
        ('counselor', 'Counselor'),
        ('therapist', 'Therapist'),
        ('social_worker', 'Social Worker'),
        ('life_coach', 'Life Coach'),
    ])
    available_times = models.JSONField(default=dict, help_text="Available time slots in JSON format")
    bio = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_specialty_display()}"


class JournalEntry(models.Model):
    """User journal entries for emotional tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    mood_rating = models.IntegerField(choices=[
        (1, 'Very Sad'),
        (2, 'Sad'),
        (3, 'Neutral'),
        (4, 'Happy'),
        (5, 'Very Happy')
    ], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        try:
            username = self.user.profile.cheerful_username
        except:
            username = self.user.username
        return f"{username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class CounselorBooking(models.Model):
    """Booking system for counselor appointments"""
    client_username = models.CharField(max_length=50, help_text="Anonymous cheerful username")
    specialist = models.ForeignKey(SpecialistProfile, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    concern = models.TextField(help_text="Brief description of the concern")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    notes = models.TextField(blank=True, help_text="Specialist notes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-time']
        unique_together = ['specialist', 'date', 'time']
    
    def __str__(self):
        return f"{self.client_username} with {self.specialist.user.get_full_name()} on {self.date} at {self.time}"


class StudyLog(models.Model):
    """Study time tracking for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    duration_minutes = models.PositiveIntegerField()
    subject = models.CharField(max_length=100, blank=True)
    log_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-log_date', '-created_at']
    
    def __str__(self):
        try:
            username = self.user.profile.cheerful_username
        except:
            username = self.user.username
        return f"{username} - {self.duration_minutes}min on {self.log_date}"


class MoodLog(models.Model):
    """PHQ-2 and GAD-2 mood tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # PHQ-2 (Patient Health Questionnaire-2)
    phq2_question1 = models.IntegerField(choices=[
        (0, 'Not at all'),
        (1, 'Several days'),
        (2, 'More than half the days'),
        (3, 'Nearly every day')
    ], help_text="Little interest or pleasure in doing things")
    
    phq2_question2 = models.IntegerField(choices=[
        (0, 'Not at all'),
        (1, 'Several days'),
        (2, 'More than half the days'),
        (3, 'Nearly every day')
    ], help_text="Feeling down, depressed, or hopeless")
    
    # GAD-2 (Generalized Anxiety Disorder-2)
    gad2_question1 = models.IntegerField(choices=[
        (0, 'Not at all'),
        (1, 'Several days'),
        (2, 'More than half the days'),
        (3, 'Nearly every day')
    ], help_text="Feeling nervous, anxious, or on edge")
    
    gad2_question2 = models.IntegerField(choices=[
        (0, 'Not at all'),
        (1, 'Several days'),
        (2, 'More than half the days'),
        (3, 'Nearly every day')
    ], help_text="Not being able to stop or control worrying")
    
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    @property
    def phq2_score(self):
        return self.phq2_question1 + self.phq2_question2
    
    @property
    def gad2_score(self):
        return self.gad2_question1 + self.gad2_question2
    
    @property
    def total_distress_score(self):
        return self.phq2_score + self.gad2_score
    
    @property
    def risk_level(self):
        """Determine risk level based on scores"""
        total = self.total_distress_score
        if total >= 6:
            return 'high'
        elif total >= 3:
            return 'moderate'
        else:
            return 'low'
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        try:
            username = self.user.profile.cheerful_username
        except:
            username = self.user.username
        return f"{username} - PHQ-2: {self.phq2_score}, GAD-2: {self.gad2_score} ({self.timestamp.strftime('%Y-%m-%d')})"


class ChatSession(models.Model):
    """Track chat sessions with the AI buddy"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        try:
            username = self.user.profile.cheerful_username
        except:
            username = self.user.username
        return f"Chat Session {self.session_id} - {username}"


class ChatMessage(models.Model):
    """Store chat messages between users and AI"""
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=[
        ('user', 'User'),
        ('ai', 'AI'),
        ('system', 'System')
    ])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_emergency = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."


class DailyMotivation(models.Model):
    """Daily motivational messages for users"""
    message = models.TextField()
    date = models.DateField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Motivation for {self.date}: {self.message[:50]}..."


class MediaPlaylist(models.Model):
    """YouTube playlists and videos for Study and Relax sections"""
    CATEGORY_CHOICES = [
        ('RELAX', 'Relaxation'),
        ('STUDY', 'Study'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('BREATHING', 'Breathing Sessions'),
        ('YOGA', 'Yoga for Relaxation'),
        ('ASMR', 'ASMR Videos'),
        ('CHILL_MUSIC', 'Chill Music'),
        ('STUDY_MUSIC', 'Study Music'),
        ('STUDY_TIPS', 'Study Tips'),
        ('MOTIVATION', 'Motivational Videos'),
    ]
    
    title = models.CharField(max_length=200, help_text="Playlist or video title")
    youtube_id = models.CharField(max_length=100, help_text="YouTube playlist ID or video ID")
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_playlist = models.BooleanField(default=True, help_text="True if it's a playlist, False if it's a single video")
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'content_type', 'order']
    
    def __str__(self):
        return f"{self.get_content_type_display()} - {self.title}"
    
    @property
    def embed_url(self):
        """Generate YouTube embed URL"""
        if self.is_playlist:
            return f"https://www.youtube.com/embed/videoseries?list={self.youtube_id}"
        else:
            return f"https://www.youtube.com/embed/{self.youtube_id}"
