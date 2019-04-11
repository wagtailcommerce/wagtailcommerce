from django.test import TestCase

from wagtailcommerce.tests.base import WithUsers


class TestGetCart(WithUsers, TestCase):
    def setUp(self):
        self.a = 1

    def test_get_cart(self):
        self.assertEqual(self.a, 1)

    def test_get_cart_2(self):
        self.assertEqual(self.a, 1)
