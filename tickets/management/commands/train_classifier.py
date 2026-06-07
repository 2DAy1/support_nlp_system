import csv
from pathlib import Path

import joblib
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from sklearn.feature_extraction.text import (
    TfidfVectorizer,
)
from sklearn.metrics import (
    accuracy_score,
    classification_report,
)
from sklearn.model_selection import (
    train_test_split,
)
from sklearn.naive_bayes import (
    MultinomialNB,
)
from sklearn.pipeline import (
    Pipeline,
)


class Command(BaseCommand):
    help = (
        'Train NLP classifier '
        'and save trained model'
    )

    DATASET_PATH = (
        Path(
            'ml/data/training_data.csv'
        )
    )

    ARTIFACTS_DIR = (
        Path(
            'ml/artifacts'
        )
    )

    MODEL_PATH = (
        ARTIFACTS_DIR
        / 'ticket_classifier.joblib'
    )

    def handle(self, *args, **options):

        dataset_path = (
            settings.BASE_DIR
            / self.DATASET_PATH
        )

        if not dataset_path.exists():
            raise CommandError(
                f'Dataset not found: {dataset_path}'
            )

        texts, categories = (
            self._load_dataset(
                dataset_path
            )
        )

        if len(texts) < 30:
            raise CommandError(
                (
                    'Dataset too small. '
                    'Need at least 30 samples.'
                )
            )

        self.stdout.write(
            (
                f'Loaded '
                f'{len(texts)} samples'
            )
        )

        model = Pipeline(
            steps=[
                (
                    'vectorizer',
                    TfidfVectorizer(
                        analyzer='char_wb',
                        lowercase=True,
                        ngram_range=(3, 5),
                        min_df=1,
                        sublinear_tf=True,
                    )
                ),
                (
                    'classifier',
                    MultinomialNB(
                        alpha=0.5,
                    ),
                ),
            ]
        )

        (
            x_train,
            x_test,
            y_train,
            y_test,
        ) = train_test_split(
            texts,
            categories,
            test_size=0.2,
            random_state=42,
            stratify=categories,
        )

        self.stdout.write(
            (
                f'Train: '
                f'{len(x_train)}'
            )
        )

        self.stdout.write(
            (
                f'Test: '
                f'{len(x_test)}'
            )
        )

        model.fit(
            x_train,
            y_train,
        )

        predictions = (
            model.predict(
                x_test
            )
        )

        accuracy = (
            accuracy_score(
                y_test,
                predictions,
            )
        )

        artifacts_dir = (
            settings.BASE_DIR
            / self.ARTIFACTS_DIR
        )

        artifacts_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        model_path = (
            settings.BASE_DIR
            / self.MODEL_PATH
        )

        joblib.dump(
            model,
            model_path,
        )

        self.stdout.write(
            ''
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f'Accuracy: '
                    f'{accuracy:.2f}'
                )
            )
        )

        self.stdout.write(
            ''
        )

        self.stdout.write(
            self._safe_console_text(
                classification_report(
                    y_test,
                    predictions,
                    zero_division=0,
                )
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    'Model saved:\n'
                    f'{model_path}'
                )
            )
        )

    def _load_dataset(
        self,
        dataset_path,
    ):
        texts = []
        categories = []

        with dataset_path.open(
            mode='r',
            encoding='utf-8',
            newline='',
        ) as file:

            reader = (
                csv.DictReader(
                    file
                )
            )

            for row in reader:

                text = (
                    row
                    .get(
                        'text',
                        ''
                    )
                    .strip()
                )

                category = (
                    row
                    .get(
                        'category',
                        ''
                    )
                    .strip()
                )

                if (
                    not text
                    or
                    not category
                ):
                    continue

                texts.append(
                    text
                )

                categories.append(
                    category
                )

        return (
            texts,
            categories,
        )

    def _safe_console_text(self, text):
        encoding = getattr(self.stdout._out, 'encoding', None) or 'utf-8'

        return text.encode(
            encoding,
            errors='replace',
        ).decode(
            encoding,
        )
