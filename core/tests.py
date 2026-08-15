from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import LibraryBook, Subscription


class SummaristPagesTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gain more knowledge')

    def test_for_you_page_loads(self):
        response = self.client.get(reverse('for_you'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Selected Book')

    def test_book_detail_page_loads(self):
        response = self.client.get(reverse('book_detail', args=['atomic-habits']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Lean Startup')

    def test_choose_plan_page_loads(self):
        response = self.client.get(reverse('choose_plan'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose your plan')

    def test_settings_page_loads(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Settings')

    def test_settings_page_uses_logged_in_sidebar_layout(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'app-layout')
        self.assertContains(response, 'sidebar__brand-wrap')
        self.assertContains(response, 'sidebar__bottom')

    def test_library_page_loads(self):
        response = self.client.get(reverse('library'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Library')

    def test_search_page_loads(self):
        response = self.client.get(reverse('search') + '?q=atomic')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search Results')

    def test_for_you_page_uses_summarist_api_data(self):
        response = self.client.get(reverse('for_you'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Lean Startup')

    def test_sidebar_links_are_clickable(self):
        response = self.client.get(reverse('for_you'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/for-you/"')
        self.assertContains(response, 'href="/library/"')
        self.assertContains(response, 'href="/settings/"')

    def test_user_registration_and_login(self):
        response = self.client.post(
            reverse('handle_auth'),
            {'action': 'register', 'email': 'newuser@example.com', 'password': 'strongpass123'},
        )
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email='newuser@example.com')
        self.assertTrue(user.is_authenticated)

    def test_library_book_can_be_saved(self):
        user = get_user_model().objects.create_user(username='libraryuser', email='library@example.com', password='pass1234')
        self.client.force_login(user)
        response = self.client.post(reverse('save_book', args=['atomic-habits']))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LibraryBook.objects.filter(user=user, book_id='f9gy1gpai8').exists())

    def test_subscription_can_be_chosen(self):
        user = get_user_model().objects.create_user(username='planuser', email='plan@example.com', password='pass1234')
        self.client.force_login(user)
        response = self.client.post(reverse('choose_plan'), {'plan': 'premium'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Subscription.objects.filter(user=user, plan='premium').exists())
