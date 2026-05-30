from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


@dataclass(frozen=True)
class ClassificationResult:
    category_name: str
    confidence: float


class TicketClassifier:
    def __init__(self):
        self.training_data = self._get_training_data()
        self.model = self._build_model()
        self._train()

    def classify(self, text: str) -> ClassificationResult:
        prediction = self.model.predict([text])[0]
        probabilities = self.model.predict_proba([text])[0]
        confidence = round(max(probabilities) * 100, 2)

        return ClassificationResult(
            category_name=prediction,
            confidence=confidence
        )

    def _build_model(self) -> Pipeline:
        return Pipeline([
            ('tfidf', TfidfVectorizer()),
            ('classifier', MultinomialNB()),
        ])

    def _train(self) -> None:
        texts = [item[0] for item in self.training_data]
        labels = [item[1] for item in self.training_data]

        self.model.fit(texts, labels)

    def _get_training_data(self) -> list[tuple[str, str]]:
        return [
            ('Не можу увійти в акаунт', 'Авторизація'),
            ('Забув пароль від особистого кабінету', 'Авторизація'),
            ('Система не приймає логін', 'Авторизація'),
            ('Не працює авторизація', 'Авторизація'),
            ('Потрібно відновити доступ до акаунта', 'Авторизація'),

            ('Не проходить оплата карткою', 'Оплата'),
            ('Платіж не був зарахований', 'Оплата'),
            ('Помилка під час оплати', 'Оплата'),
            ('Гроші списались але послуга не активувалась', 'Оплата'),
            ('Не можу оплатити замовлення', 'Оплата'),

            ('Сайт не відкривається', 'Технічна помилка'),
            ('Сторінка зависає після входу', 'Технічна помилка'),
            ('Виникає помилка 500', 'Технічна помилка'),
            ('Не працює кнопка збереження', 'Технічна помилка'),
            ('Сервер не відповідає', 'Технічна помилка'),

            ('Як змінити налаштування профілю', 'Консультація'),
            ('Підкажіть як користуватися сервісом', 'Консультація'),
            ('Де знайти історію замовлень', 'Консультація'),
            ('Як змінити електронну пошту', 'Консультація'),
            ('Потрібна консультація щодо функціоналу', 'Консультація'),

            ('Хочу залишити відгук', 'Інше'),
            ('Є пропозиція щодо покращення сервісу', 'Інше'),
            ('Питання не стосується роботи системи', 'Інше'),
            ('Інше звернення до адміністрації', 'Інше'),
            ('Хочу повідомити загальну інформацію', 'Інше'),
        ]