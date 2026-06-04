import json

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from tickets.models import Category
from tickets.services.classifier import TicketClassifier
from tickets.services.routing import TicketRoutingService


@method_decorator(csrf_exempt, name='dispatch')
class ClassifyTicketApiView(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        data = self._parse_json(request)

        if data is None:
            return JsonResponse(
                {
                    'error': 'Invalid JSON'
                },
                status=400
            )

        title = data.get('title', '')
        text = data.get('text', '')

        full_text = f'{title} {text}'.strip()

        if not full_text:
            return JsonResponse(
                {
                    'error': 'title or text required'
                },
                status=400
            )

        classifier = TicketClassifier()

        result = classifier.classify(full_text)

        confidence = float(result.confidence)

        category_name = result.category_name

        if confidence < TicketRoutingService.MIN_CONFIDENCE:
            category_name = 'Інше'

        category = (
            Category.objects
            .select_related('department')
            .filter(name=category_name)
            .first()
        )

        return JsonResponse(
            {
                'input': full_text,
                'predicted_category': result.category_name,
                'final_category': category_name,
                'department': (
                    category.department.name
                    if category
                    else None
                ),
                'confidence': round(confidence, 2),
            }
        )

    def _parse_json(self, request):
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None