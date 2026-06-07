import json

from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from tickets.models import CompanyApiKey, Source
from tickets.services.routing import TicketRoutingService


@method_decorator(csrf_exempt, name='dispatch')
class TicketCreateApiView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        api_key = self._get_api_key(request)

        if api_key is None:
            return JsonResponse(
                {'error': 'Invalid or missing API key.'},
                status=401,
            )

        data = self._parse_json(request)

        if data is None:
            return JsonResponse(
                {'error': 'Invalid JSON body.'},
                status=400,
            )

        validation_error = self._validate_payload(data)

        if validation_error:
            return JsonResponse(
                {'error': validation_error},
                status=400,
            )

        source = self._get_source(
            company=api_key.company,
            source_name=data.get('source'),
        )

        service = TicketRoutingService()

        ticket = service.create_ticket(
            company=api_key.company,
            source=source,
            title=data['title'],
            text=data['text'],
            external_id=data.get('external_id', ''),
            author_name=data.get('author_name', ''),
            author_email=data.get('author_email', ''),
            rating=data.get('rating'),
            raw_payload=data,
        )

        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=['last_used_at'])

        return JsonResponse(
            {
                'id': ticket.id,
                'company': ticket.company.name,
                'source': ticket.source.name if ticket.source else None,
                'title': ticket.title,
                'category': ticket.category.name if ticket.category else None,
                'department': (
                    ticket.department.name
                    if ticket.department
                    else None
                ),
                'status': ticket.status,
                'confidence': round(ticket.confidence, 2),
            },
            status=201,
        )

    def _get_api_key(self, request):
        raw_key = request.headers.get('X-API-Key')

        if not raw_key:
            return None

        return (
            CompanyApiKey.objects
            .select_related('company')
            .filter(
                key=raw_key,
                is_active=True,
                company__is_active=True,
            )
            .first()
        )

    def _parse_json(self, request):
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None

    def _validate_payload(self, data):
        if not data.get('title'):
            return 'Field "title" is required.'

        if not data.get('text'):
            return 'Field "text" is required.'

        rating = data.get('rating')

        if rating is not None:
            try:
                rating = int(rating)
            except (TypeError, ValueError):
                return 'Field "rating" must be an integer.'

            if rating < 1 or rating > 5:
                return 'Field "rating" must be between 1 and 5.'

        return None

    def _get_source(self, company, source_name):
        if not source_name:
            return None

        return (
            Source.objects
            .filter(
                company=company,
                name=source_name,
                is_active=True,
            )
            .first()
        )


@method_decorator(csrf_exempt, name='dispatch')
class ClassifyTicketApiView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        data = self._parse_json(request)

        if data is None:
            return JsonResponse(
                {'error': 'Invalid JSON body.'},
                status=400,
            )

        title = data.get('title', '')
        text = data.get('text', '')
        full_text = f'{title} {text}'.strip()

        if not full_text:
            return JsonResponse(
                {'error': 'Field "title" or "text" is required.'},
                status=400,
            )

        service = TicketRoutingService()
        result = service.classifier.classify(full_text)

        return JsonResponse(
            {
                'predicted_category': result.category_name,
                'confidence': round(float(result.confidence), 2),
            }
        )

    def _parse_json(self, request):
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None
