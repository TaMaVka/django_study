"""Forms with validation for VisualIQ application."""

import re
from django import forms
from .models import TheoryItem


class TheorySubmitForm(forms.ModelForm):
    """Form for submitting a new educational article."""

    class Meta:
        model = TheoryItem
        fields = ['title', 'content']
        labels = {
            'title': 'Заголовок',
            'content': 'Текст статьи (Markdown)',
        }
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control',
                       'placeholder': 'Название статьи'}
            ),
            'content': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 8,
                       'placeholder': 'Подробный текст...'}
            ),
        }

    def clean_title(self):
        """Validate that title is at least 3 characters."""
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 3:
            raise forms.ValidationError(
                'Заголовок слишком короткий. Минимум 3 символа.'
            )
        return title

    def clean_content(self):
        """Validate that content is at least 50 characters."""
        content = self.cleaned_data.get('content', '')
        if len(content) < 50:
            raise forms.ValidationError(
                'Статья слишком короткая для образовательного материала. '
                'Добавьте больше деталей (минимум 50 символов).'
            )
        return content


class HexAnswerForm(forms.Form):
    """Form for submitting a HEX color code guess."""

    hex_code = forms.CharField(
        max_length=7,
        label='Ваш ответ (HEX-код)',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-lg',
                   'placeholder': '#FF5733'}
        ),
    )

    def clean_hex_code(self):
        """Validate HEX color code format using regex."""
        value = self.cleaned_data.get('hex_code', '')
        pattern = r'^#[0-9A-Fa-f]{6}$'
        if not re.match(pattern, value):
            raise forms.ValidationError(
                'Неверный формат. Ожидается код вида #RRGGBB, '
                'состоящий из символа # и 6 букв A-F или цифр 0-9.'
            )
        return value.upper()