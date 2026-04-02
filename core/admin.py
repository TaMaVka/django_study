"""Admin panel configuration for VisualIQ models."""

from django.contrib import admin
from .models import (
    UserProfile, TheoryItem, ArticleImage, AITask, GameSession
)


class ArticleImageInline(admin.TabularInline):
    """Inline for uploading images to articles."""

    model = ArticleImage
    extra = 1
    readonly_fields = ('markdown_syntax',)

    def markdown_syntax(self, obj):
        """Show copyable markdown tag after image is saved."""
        if obj.pk and obj.image:
            return f'![{obj.caption}]({obj.image.url})'
        return '— сохраните статью, чтобы получить тег —'
    markdown_syntax.short_description = 'Скопируйте в текст статьи'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin view for user profiles."""

    list_display = ('user', 'coins')
    search_fields = ('user__username',)


@admin.register(TheoryItem)
class TheoryItemAdmin(admin.ModelAdmin):
    """Admin view for educational articles."""

    list_display = ('title', 'price', 'is_approved', 'created_at')
    list_filter = ('is_approved',)
    list_editable = ('is_approved', 'price')
    search_fields = ('title',)
    inlines = [ArticleImageInline]


@admin.register(AITask)
class AITaskAdmin(admin.ModelAdmin):
    """Admin view for AI detection tasks."""

    list_display = ('id', 'correct_answer')


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    """Admin view for game session history."""

    list_display = ('user', 'game_type', 'points_earned', 'created_at')
    list_filter = ('game_type',)