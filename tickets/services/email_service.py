from django.core.mail import send_mail
from django.conf import settings


class EmailService:

    @staticmethod
    def notify_manager(ticket):

        subject = (
            f'Нове звернення #{ticket.id}'
        )

        message = f'''
Компанія:
{ticket.company}

Категорія:
{ticket.category}

Відділ:
{ticket.department}

Текст:
{ticket.text}
'''

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [
                settings.MANAGER_EMAIL
            ],
            fail_silently=False,
        )

    @staticmethod
    def notify_status(ticket):

        if not ticket.client_email:
            return

        send_mail(
            f'Статус звернення #{ticket.id}',
            f'''
Новий статус:

{ticket.status}
''',
            settings.DEFAULT_FROM_EMAIL,
            [
                ticket.client_email
            ],
            fail_silently=True,
        )