from django import forms

from tickets.models import Ticket, TicketComment


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'title',
            'text',
        )
        labels = {
            'title': 'Тема звернення',
            'text': 'Текст звернення',
        }
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                }
            ),
            'text': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                }
            ),
        }


class TicketStatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = (
            'status',
            'assigned_user',
        )
        labels = {
            'status': 'Статус',
            'assigned_user': 'Відповідальний менеджер',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
            })


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = (
            'text',
            'is_internal',
        )
        labels = {
            'text': 'Коментар',
            'is_internal': 'Внутрішній коментар',
        }
        widgets = {
            'text': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Додайте робочий коментар до звернення...',
                }
            ),
            'is_internal': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                }
            ),
        }