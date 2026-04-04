"""Views for the VisualIQ application."""

import math
import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages as django_messages

from .models import UserProfile, TheoryItem, GameSession
from .forms import TheorySubmitForm, HexAnswerForm, HSLAnswerForm

MAX_RGB_DISTANCE = 441.67
MAX_HSL_DISTANCE = math.sqrt(3)


def calculate_game_points(accuracy):
    """Convert accuracy percentage to coin reward."""
    if accuracy >= 90:
        return 5
    if accuracy >= 70:
        return 3
    if accuracy >= 50:
        return 2
    return 0


def _update_coins(user, points, game_type):
    """Save coins and create game session record."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.coins += points
    profile.save()
    GameSession.objects.create(
        user=user, game_type=game_type, points_earned=points
    )
    return profile


# --- Pages ---

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
                'Недостаточно монет! Заработайте в тренажерах.'
            )
            return redirect('theory_list')

    return render(request, 'core/theory_detail.html', {
        'item': item,
        'is_unlocked': is_unlocked,
        'profile': profile,
    })


@login_required
def theory_submit(request):
    """Handle article submission with author tracking."""
    if request.method == 'POST':
        form = TheorySubmitForm(request.POST)
        if form.is_valid():
            theory = form.save(commit=False)
            theory.author = request.user
            theory.is_approved = False
            theory.save()
            django_messages.success(
                request,
                'Спасибо! Статья отправлена на модерацию.'
            )
            return redirect('theory_list')
    else:
        form = TheorySubmitForm()
    return render(request, 'core/theory_submit.html', {'form': form})


# --- HEX game ---

def generate_random_hex():
    """Generate a random HEX color code."""
    red = random.randint(0, 255)
    green = random.randint(0, 255)
    blue = random.randint(0, 255)
    return f'#{red:02X}{green:02X}{blue:02X}'


def hex_color_distance(hex1, hex2):
    """Calculate Euclidean distance between two HEX colors."""
    r1 = int(hex1[1:3], 16)
    g1 = int(hex1[3:5], 16)
    b1 = int(hex1[5:7], 16)
    r2 = int(hex2[1:3], 16)
    g2 = int(hex2[3:5], 16)
    b2 = int(hex2[5:7], 16)
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


@login_required
def hex_game(request):
    """Handle the HEX Sniper game with quadratic scoring."""
    if request.method == 'POST':
        form = HexAnswerForm(request.POST)
        correct_hex = request.session.get('correct_hex', '#000000')

        if form.is_valid():
            user_hex = form.cleaned_data['hex_code']
            distance = hex_color_distance(correct_hex, user_hex)
            ratio = distance / MAX_RGB_DISTANCE
            accuracy = max(0, 100 * (1 - ratio) ** 2)
            points = calculate_game_points(accuracy)

            _update_coins(request.user, points, 'HEX')

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


# --- HSL game ---

def hsl_color_distance(h1, s1, l1, h2, s2, l2):
    """Calculate normalized distance between two HSL colors."""
    hue_diff = min(abs(h1 - h2), 360 - abs(h1 - h2))
    h_norm = hue_diff / 180.0
    s_norm = abs(s1 - s2) / 100.0
    l_norm = abs(l1 - l2) / 100.0
    return math.sqrt(h_norm ** 2 + s_norm ** 2 + l_norm ** 2)


@login_required
def hsl_game(request):
    """Handle the HSL Master game with quadratic scoring."""
    if request.method == 'POST':
        form = HSLAnswerForm(request.POST)
        cor_h = request.session.get('correct_h', 0)
        cor_s = request.session.get('correct_s', 50)
        cor_l = request.session.get('correct_l', 50)

        if form.is_valid():
            usr_h = form.cleaned_data['hue']
            usr_s = form.cleaned_data['saturation']
            usr_l = form.cleaned_data['lightness']

            distance = hsl_color_distance(
                cor_h, cor_s, cor_l, usr_h, usr_s, usr_l
            )
            ratio = distance / MAX_HSL_DISTANCE
            accuracy = max(0, 100 * (1 - ratio) ** 2)
            points = calculate_game_points(accuracy)

            _update_coins(request.user, points, 'HSL')

            new_h = random.randint(0, 359)
            new_s = random.randint(30, 90)
            new_l = random.randint(25, 75)
            request.session['correct_h'] = new_h
            request.session['correct_s'] = new_s
            request.session['correct_l'] = new_l

            return render(request, 'core/hsl_game.html', {
                'form': HSLAnswerForm(),
                'h': new_h, 's': new_s, 'l': new_l,
                'result': True,
                'correct_h': cor_h, 'correct_s': cor_s,
                'correct_l': cor_l,
                'user_h': usr_h, 'user_s': usr_s,
                'user_l': usr_l,
                'accuracy': round(accuracy, 1),
                'points': points,
            })

        return render(request, 'core/hsl_game.html', {
            'form': form,
            'h': cor_h, 's': cor_s, 'l': cor_l,
        })

    hue = random.randint(0, 359)
    sat = random.randint(30, 90)
    lit = random.randint(25, 75)
    request.session['correct_h'] = hue
    request.session['correct_s'] = sat
    request.session['correct_l'] = lit
    return render(request, 'core/hsl_game.html', {
        'form': HSLAnswerForm(),
        'h': hue, 's': sat, 'l': lit,
    })


# --- Auth ---

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
