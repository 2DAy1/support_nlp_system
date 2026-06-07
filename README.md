# Support NLP System

B2B support ticket routing system with NLP classification.

Support NLP System receives customer requests from external systems through an API, classifies ticket text with a trained NLP model, routes tickets to the correct company department, and gives managers a dashboard for daily support operations.

## Main Features

- Company-based ticket management
- API-key integration for external systems
- Automatic NLP classification
- Automatic routing to departments
- Manager dashboard
- Ticket list and filtering
- Status workflow
- Audit log for ticket events
- Internal comments
- Swagger API documentation
- PostgreSQL support
- Trained ML model
- Automated tests

## Technologies

- Python
- Django
- Django REST Framework
- PostgreSQL
- Scikit-learn
- TF-IDF
- Multinomial Naive Bayes
- Bootstrap
- Swagger / drf-spectacular
- WhiteNoise
- Gunicorn
- Render

## Local Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Create `.env` from `.env.example`.
5. Run migrations.
6. Train the classifier if the model artifact is missing.
7. Seed demo data if needed.
8. Create a superuser.
9. Start the development server.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py train_classifier
python manage.py seed_demo_data --username test_user
python manage.py createsuperuser
python manage.py runserver
```

On Linux or macOS, activate the virtual environment with:

```bash
source .venv/bin/activate
```

## Common Commands

```bash
python manage.py migrate
python manage.py train_classifier
python manage.py seed_demo_data --username test_user
python manage.py test
python manage.py runserver
```

## API Usage

Create a ticket through the API with the company API key in the `X-API-Key` header.

```bash
curl -X POST http://127.0.0.1:8000/api/tickets/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-company-api-key" \
  -d "{
    \"source\": \"Website form\",
    \"external_id\": \"ticket-001\",
    \"author_name\": \"Client Name\",
    \"author_email\": \"client@example.com\",
    \"rating\": 4,
    \"title\": \"Cannot log in\",
    \"text\": \"The system does not accept my password\"
  }"
```

Classify text without creating a ticket:

```bash
curl -X POST http://127.0.0.1:8000/api/classify/ \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Cannot log in\",
    \"text\": \"The system does not accept my password\"
  }"
```

## Swagger

Swagger UI is available at:

```text
http://127.0.0.1:8000/api/docs/
```

The OpenAPI schema is available at:

```text
http://127.0.0.1:8000/api/schema/
```

## Testing

Run the full test suite:

```bash
python manage.py test
```

## NLP Model

Training data is stored in `ml/data/training_data.csv`.

The trained classifier artifact is stored in:

```text
ml/artifacts/ticket_classifier.joblib
```

If the model artifact is missing, retrain it:

```bash
python manage.py train_classifier
```

## Deployment On Render

This project is prepared for deployment on Render without Docker.

Render build command:

```bash
./build.sh
```

Render start command:

```bash
gunicorn config.wsgi:application
```

Required Render environment variables:

```text
SECRET_KEY
DEBUG
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
DB_NAME
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
SEED_DEMO_DATA
```

Example production values:

```text
DEBUG=False
SEED_DEMO_DATA=True
ALLOWED_HOSTS=your-render-service.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-render-service.onrender.com
```

`build.sh` installs dependencies, collects static files, runs migrations, and seeds demo data only when `SEED_DEMO_DATA=True`.

## Static Files

Static files are served with WhiteNoise. Production static files are collected into:

```text
staticfiles/
```
