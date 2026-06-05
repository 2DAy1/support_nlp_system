from dataclasses import dataclass
from pathlib import Path

import joblib
from django.conf import settings


@dataclass(frozen=True)
class ClassificationResult:
    category_name: str
    confidence: float


class TicketClassifier:
    MODEL_PATH = Path('ml/artifacts/ticket_classifier.joblib')

    def __init__(self):
        self.model = self._load_model()

    def classify(self, text: str) -> ClassificationResult:
        prepared_text = text.strip()

        if not prepared_text:
            return ClassificationResult(
                category_name='Інше',
                confidence=0,
            )

        probabilities = self.model.predict_proba([prepared_text])[0]
        classes = self.model.classes_

        best_index = probabilities.argmax()
        category_name = classes[best_index]
        confidence = float(probabilities[best_index] * 100)

        return ClassificationResult(
            category_name=category_name,
            confidence=round(confidence, 2),
        )

    def _load_model(self):
        model_path = settings.BASE_DIR / self.MODEL_PATH

        if not model_path.exists():
            raise FileNotFoundError(
                f'Classifier model not found: {model_path}. '
                f'Run: py manage.py train_classifier'
            )

        return joblib.load(model_path)