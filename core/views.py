"""Views for the VisualIQ application."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages as django_messages

from .models import UserProfile, TheoryItem, GameSession


def home(request):
    """Display the main dashboard page."""
    context = {}
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        sessions = GameSession.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        context['profile'] = profile
        context['sessions'] = sessions
    return render(request, 'core/home.html', context)


def theory_list(request):
    """Display list of approved articles."""
    items = TheoryItem.objects.filter(is_approved=True)
    return render(request, 'core/theory_list.html', {'items': items})


@login_required
def theory_detail(request, pk):
    """Display article with purchase logic."""
    item = get_object_or_404(TheoryItem, pk=pk, is_approved=True)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    is_unlocked = (
        item.price == 0
        or profile.unlocked_theories.filter(pk=item.pk).exists()
    )

    if request.method == 'POST' and not is_unlocked:
        if profile.coins >= item.price:
            profile.coins -= item.price
            profile.save()
            profile.unlocked_theories.add(item)
            django_messages.success(
                request,
                f'Списано {item.price} монет. Статья разблокирована!'
            )
            is_unlocked = True
        else:
            django_messages.error(
                request,
                'Недостаточно монет! Пройдите тренажеры для заработка.'
            )
            return redirect('theory_list')

    return render(request, 'core/theory_detail.html', {
        'item': item,
        'is_unlocked': is_unlocked,
        'profile': profile,
    })


def register_view(request):
    """Handle new user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, coins=5)
            login(request, user)
            django_messages.success(
                request, 'Добро пожаловать в VisualIQ!'
            )
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})