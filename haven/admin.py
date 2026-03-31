from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, SpecialistProfile, JournalEntry, CounselorBooking,
    StudyLog, MoodLog, ChatSession, ChatMessage, DailyMotivation,
    MediaPlaylist, StudyBackgroundMusic, StudyVideo
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(SpecialistProfile)
class SpecialistProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'experience_years', 'is_verified', 'created_at']
    list_filter = ['specialty', 'is_verified', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at']


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'mood_rating', 'created_at']
    list_filter = ['mood_rating', 'created_at']
    search_fields = ['user__profile__cheerful_username', 'text']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CounselorBooking)
class CounselorBookingAdmin(admin.ModelAdmin):
    list_display = ['client_username', 'specialist', 'date', 'time', 'status']
    list_filter = ['status', 'date', 'specialist__specialty']
    search_fields = ['client_username', 'concern']
    readonly_fields = ['created_at']


@admin.register(StudyLog)
class StudyLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'duration_minutes', 'subject', 'log_date']
    list_filter = ['log_date', 'subject']
    search_fields = ['user__profile__cheerful_username', 'subject', 'notes']
    readonly_fields = ['created_at']


@admin.register(MoodLog)
class MoodLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'phq2_score', 'gad2_score', 'risk_level', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user__profile__cheerful_username']
    readonly_fields = ['phq2_score', 'gad2_score', 'total_distress_score', 'risk_level', 'timestamp']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'started_at', 'last_activity', 'is_active']
    list_filter = ['is_active', 'started_at']
    search_fields = ['user__profile__cheerful_username', 'session_id']
    readonly_fields = ['started_at', 'last_activity']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'message_type', 'is_emergency', 'timestamp']
    list_filter = ['message_type', 'is_emergency', 'timestamp']
    search_fields = ['content', 'session__user__profile__cheerful_username']
    readonly_fields = ['timestamp']


@admin.register(DailyMotivation)
class DailyMotivationAdmin(admin.ModelAdmin):
    list_display = ['date', 'is_active', 'created_at']
    list_filter = ['is_active', 'date']
    search_fields = ['message']
    readonly_fields = ['created_at']


@admin.register(MediaPlaylist)
class MediaPlaylistAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'category', 'is_playlist', 'order', 'is_active']
    list_filter = ['category', 'content_type', 'is_active', 'is_playlist']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'embed_url']
    list_editable = ['order', 'is_active']
    ordering = ['category', 'content_type', 'order']


@admin.register(StudyBackgroundMusic)
class StudyBackgroundMusicAdmin(admin.ModelAdmin):
    list_display  = ['title', 'order', 'is_active', 'created_at']
    list_filter   = ['is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title']
    readonly_fields = ['created_at', 'src']
    fieldsets = (
        (None, {
            'fields': ('title', 'order', 'is_active')
        }),
        ('Audio Source (choose one)', {
            'description': 'Upload a file OR paste a direct audio URL. File takes priority.',
            'fields': ('audio_file', 'audio_url', 'src'),
        }),
    )


@admin.register(StudyVideo)
class StudyVideoAdmin(admin.ModelAdmin):
    list_display  = ['title', 'category', 'order', 'is_active', 'video_id', 'created_at']
    list_filter   = ['category', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'youtube_url']
    readonly_fields = ['video_id', 'embed_url', 'created_at']
    fieldsets = (
        (None, {
            'fields': ('title', 'category', 'youtube_url', 'order', 'is_active')
        }),
        ('Resolved (read-only)', {
            'fields': ('video_id', 'embed_url'),
        }),
    )
