from django.test import TestCase

from wagtailcommerce.tests.customuser.models import EmailUser


class WithUsers(object):
    def setUp(self):
        super(WithUsers, self).setUp()

        self.customer_user = EmailUser(
            email='testuser@test.com',
            is_active=True,
            is_staff=False,
            is_superuser=False,
            first_name='Test',
            last_name='Test'
        )

        self.custom_user.set_password('test')
        self.custom_user.save()

        self.superuser = EmailUser.objects.create(
            email='superuser@test.com',
            is_active=True,
            is_staff=True,
            is_superuser=True,
            first_name='Superuser',
            last_name='Test'
        )

        self.staff_user.set_password('test')
        self.staff_user.save()
