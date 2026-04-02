"""Views for the VisualIQ application."""

import math
import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages as django_messages

from .models import UserProfile, TheoryItem, GameSession
from .forms import TheorySubmitForm, HexAnswerForm


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


@login_required
def theory_submit(request):
    """Handle article submission."""
    if request.method == 'POST':
        form = TheorySubmitForm(request.POST)
        if form.is_valid():
            theory = form.save(commit=False)
            theory.is_approved = False
            theory.save()
            django_messages.success(
                request,
                'Спасибо! Ваша статья отправлена на модерацию.'
            )
            return redirect('theory_list')
    else:
        form = TheorySubmitForm()
    return render(request, 'core/theory_submit.html', {'form': form})


def generate_random_hex():
    """Generate a random HEX color code string."""
    red = random.randint(0, 255)
    green = random.randint(0, 255)
    blue = random.randint(0, 255)
    return f'#{red:02X}{green:02X}{blue:02X}'


def hex_color_distance(hex1, hex2):
    """Calculate Euclidean distance between two HEX colors."""
    r1, g1, b1 = int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16)
    r2, g2, b2 = int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16)
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def calculate_hex_points(accuracy):
    """Convert accuracy percentage to coin reward."""
    if accuracy >= 90:
        return 5
    if accuracy >= 70:
        return 3
    if accuracy >= 50:
        return 2
    return 0


@login_required
def hex_game(request):
    """Handle the HEX Sniper game."""
    max_rgb_distance = 441.67

    if request.method == 'POST':
        form = HexAnswerForm(request.POST)
        correct_hex = request.session.get('correct_hex', '#000000')

        if form.is_valid():
            user_hex = form.cleaned_data['hex_code']
            distance = hex_color_distance(correct_hex, user_hex)
            accuracy = max(0, 100 - (distance / max_rgb_distance * 100))
            points = calculate_hex_points(accuracy)

            profile, _ = UserProfile.objects.get_or_create(
                user=request.user
            )
            profile.coins += points
            profile.save()

            GameSession.objects.create(
                user=request.user,
                game_type='HEX',
                points_earned=points,
            )

            new_color = generate_random_hex()
            request.session['correct_hex'] = new_color

            return render(request, 'core/hex_game.html', {
                'form': HexAnswerForm(),
                'color': new_color,
                'result': True,
                'correct_hex': correct_hex,
                'user_hex': user_hex,
                'accuracy': round(accuracy, 1),
                'points': points,
            })

        return render(request, 'core/hex_game.html', {
            'form': form,
            'color': correct_hex,
        })

    color = generate_random_hex()
    request.session['correct_hex'] = color
    return render(request, 'core/hex_game.html', {
        'form': HexAnswerForm(),
        'color': color,
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