from django import forms

from tickets.models import Ticket


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('title', 'text')
        labels = {
            'title': 'Тема звернення',
            'text': 'Текст звернення',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Наприклад: Проблема з входом',
            }),
            'text': forms.Textarea(attrs={
                'placeholder': 'Опишіть проблему детально',
                'rows': 6,
            }),
        }


class TicketStatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('status',)
        labels = {
            'status': 'Статус звернення',
        }