from django.contrib.auth.models import User
from django.test import TestCase

from tickets.models import (
    Category,
    Company,
    CompanyApiKey,
    Department,
    Source,
    UserProfile,
)


class BaseTicketTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            name='Test Company',
            description='Test company',
        )

        cls.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123',
        )

        cls.profile = UserProfile.objects.create(
            user=cls.user,
            company=cls.company,
            role=UserProfile.Role.COMPANY_ADMIN,
        )

        cls.source = Source.objects.create(
            company=cls.company,
            name='Website form',
            source_type=Source.SourceType.WEBSITE,
        )

        cls.api_key = CompanyApiKey.objects.create(
            company=cls.company,
            name='Test API key',
        )

        cls.auth_department = Department.objects.create(
            company=cls.company,
            name='Відділ авторизації',
        )

        cls.payment_department = Department.objects.create(
            company=cls.company,
            name='Фінансовий відділ',
        )

        cls.tech_department = Department.objects.create(
            company=cls.company,
            name='Технічна підтримка',
        )

        cls.consulting_department = Department.objects.create(
            company=cls.company,
            name='Консультаційний відділ',
        )

        cls.other_department = Department.objects.create(
            company=cls.company,
            name='Загальний відділ підтримки',
        )

        Category.objects.create(
            company=cls.company,
            name='Авторизація',
            department=cls.auth_department,
        )

        Category.objects.create(
            company=cls.company,
            name='Оплата',
            department=cls.payment_department,
        )

        Category.objects.create(
            company=cls.company,
            name='Технічна помилка',
            department=cls.tech_department,
        )

        Category.objects.create(
            company=cls.company,
            name='Консультація',
            department=cls.consulting_department,
        )

        Category.objects.create(
            company=cls.company,
            name='Інше',
            department=cls.other_department,
        )


class TicketModelTests(BaseTicketTestCase):
    def test_company_can_be_created(self):
        self.assertEqual(self.company.name, 'Test Company')
        self.assertTrue(self.company.is_active)

    def test_source_belongs_to_company(self):
        self.assertEqual(self.source.company, self.company)
        self.assertEqual(self.source.source_type, Source.SourceType.WEBSITE)

    def test_api_key_belongs_to_company(self):
        self.assertEqual(self.api_key.company, self.company)
        self.assertTrue(self.api_key.key)
        self.assertTrue(self.api_key.is_active)

    def test_user_profile_belongs_to_company(self):
        self.assertEqual(self.profile.company, self.company)
        self.assertTrue(self.profile.is_company_admin)
