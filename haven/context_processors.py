"""
haven/context_processors.py
────────────────────────────
Injects `is_counselor` and `is_student` into every template context
so templates can branch on role without extra view logic.
"""


def user_role(request):
    """Add role flags to every template context."""
    if not request.user.is_authenticated:
        return {'is_counselor': False, 'is_student': False}

    is_counselor = hasattr(request.user, 'specialistprofile')
    return {
        'is_counselor': is_counselor,
        'is_student':   not is_counselor,
    }
