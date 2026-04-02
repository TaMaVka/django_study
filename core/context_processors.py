"""Custom context processors for VisualIQ templates."""
from .models import UserProfile


def user_coins(request):
    """Add user coin balance to all template contexts."""
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return {'user_coins': profile.coins}
    return {'user_coins': 0}