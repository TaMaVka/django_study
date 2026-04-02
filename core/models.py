"""Database models for VisualIQ application."""

import markdown as md
from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe


class TheoryItem(models.Model):
    """Educational article available in the catalog."""

    title = models.CharField(max_length=200, verbose_name='Заголовок')
    cover = models.ImageField(
        upload_to='covers/', blank=True, verbose_name='Обложка'
    )
    content = models.TextField(verbose_name='Содержание (Markdown)')
    price = models.IntegerField(default=1, verbose_name='Цена (монеты)')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрено')
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-created_at']

    def __str__(self):
        return str(self.title)

    def content_as_html(self):
        """Convert markdown content to safe HTML."""
        return mark_safe(md.markdown(
            self.content, extensions=['extra', 'nl2br']
        ))


class ArticleImage(models.Model):
    """Image attached to a theory article for use in markdown content."""

    article = models.ForeignKey(
        TheoryItem, on_delete=models.CASCADE, related_name='images'
    )
    image = models.ImageField(
        upload_to='articles/', verbose_name='Изображение'
    )
    caption = models.CharField(
        max_length=200, blank=True, verbose_name='Подпись'
    )

    class Meta:
        verbose_name = 'Изображение статьи'
        verbose_name_plural = 'Изображения статей'

    def __str__(self):
        return self.caption or f'Изображение #{self.pk}'


class UserProfile(models.Model):
    """Extended user profile with coin balance."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    coins = models.IntegerField(default=5, verbose_name='Монеты')
    unlocked_theories = models.ManyToManyField(
        TheoryItem, blank=True, related_name='unlocked_by',
        verbose_name='Разблокированные статьи'
    )

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'{self.user.username} ({self.coins} монет)'


class AITask(models.Model):
    """Task with two face images for AI detection game."""

    ANSWER_CHOICES = [('A', 'Изображение A'), ('B', 'Изображение B')]

    image_a = models.ImageField(
        upload_to='ai_faces/', verbose_name='Изображение A'
    )
    image_b = models.ImageField(
        upload_to='ai_faces/', verbose_name='Изображение B'
    )
    correct_answer = models.CharField(
        max_length=1, choices=ANSWER_CHOICES,
        verbose_name='Где ИИ'
    )
    explanation = models.TextField(verbose_name='Объяснение')

    class Meta:
        verbose_name = 'AI-задача'
        verbose_name_plural = 'AI-задачи'

    def __str__(self):
        return f'AI-задача #{self.pk}'


class GameSession(models.Model):
    """Record of a single game played by a user."""

    GAME_TYPES = [('HEX', 'HEX-Снайпер'), ('AI', 'Детектор ИИ')]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='game_sessions'
    )
    game_type = models.CharField(
        max_length=3, choices=GAME_TYPES, verbose_name='Тип игры'
    )
    points_earned = models.IntegerField(
        default=0, verbose_name='Заработано монет'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата игры'
    )

    class Meta:
        verbose_name = 'Игровая сессия'
        verbose_name_plural = 'Игровые сессии'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'{self.user.username} — {self.get_game_type_display()} '
            f'(+{self.points_earned})'
        )