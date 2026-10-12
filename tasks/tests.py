from datetime import date, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Task


class TaskTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice', password='pw12345!')
        self.bob = User.objects.create_user('bob', password='pw12345!')
        d = date.today()
        self.t1 = Task.objects.create(user=self.alice, title='Late', status='pending', priority=3, due_date=d + timedelta(days=5))
        self.t2 = Task.objects.create(user=self.alice, title='Soon', status='completed', priority=1, due_date=d + timedelta(days=1))
        self.t3 = Task.objects.create(user=self.bob, title='Bob task', due_date=d)

    def test_login_required(self):
        self.assertEqual(self.client.get(reverse('task_list')).status_code, 302)

    def test_only_own_tasks_ordered_by_due_date(self):
        self.client.login(username='alice', password='pw12345!')
        tasks = list(self.client.get(reverse('task_list')).context['tasks'])
        self.assertEqual(tasks, [self.t2, self.t1])

    def test_filters_and_exclude(self):
        self.client.login(username='alice', password='pw12345!')
        r = self.client.get(reverse('task_list'), {'status': 'pending'})
        self.assertEqual(list(r.context['tasks']), [self.t1])
        r = self.client.get(reverse('task_list'), {'priority': 1})
        self.assertEqual(list(r.context['tasks']), [self.t2])
        r = self.client.get(reverse('task_list'), {'hide_completed': 'on'})
        self.assertEqual(list(r.context['tasks']), [self.t1])

    def test_cannot_view_other_users_task(self):
        self.client.login(username='alice', password='pw12345!')
        self.assertEqual(self.client.get(reverse('task_detail', args=[self.t3.pk])).status_code, 404)


class AuthTests(TestCase):
    def test_register_logs_in_and_redirects(self):
        r = self.client.post(reverse('register'), {
            'username': 'newbie', 'email': 'n@example.com',
            'password1': 'Str0ng!Pass92', 'password2': 'Str0ng!Pass92'})
        self.assertRedirects(r, reverse('task_list'))
        self.assertTrue(User.objects.filter(username='newbie').exists())
        self.assertEqual(self.client.get(reverse('task_list')).status_code, 200)

    def test_register_validation_errors(self):
        User.objects.create_user('taken', 'a@example.com', 'x')
        r = self.client.post(reverse('register'), {
            'username': 'taken', 'email': 'a@example.com',
            'password1': 'abc', 'password2': 'xyz'})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['form'].errors)

    def test_login_logout(self):
        User.objects.create_user('sam', 's@example.com', 'Str0ng!Pass92')
        r = self.client.post(reverse('login'), {'username': 'sam', 'password': 'Str0ng!Pass92'})
        self.assertRedirects(r, reverse('task_list'))
        # logged-in users skip the login page
        self.assertEqual(self.client.get(reverse('login')).status_code, 302)
        r = self.client.post(reverse('logout'))
        self.assertRedirects(r, reverse('login'))
        self.assertEqual(self.client.get(reverse('task_list')).status_code, 302)

    def test_wrong_password(self):
        User.objects.create_user('sam', 's@example.com', 'Str0ng!Pass92')
        r = self.client.post(reverse('login'), {'username': 'sam', 'password': 'nope'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'errorbox')

    def test_complete_task(self):
        u = User.objects.create_user('sam', 's@example.com', 'Str0ng!Pass92')
        t = Task.objects.create(user=u, title='x', due_date=date.today())
        self.client.login(username='sam', password='Str0ng!Pass92')
        self.client.post(reverse('task_complete', args=[t.pk]))
        t.refresh_from_db()
        self.assertEqual(t.status, 'completed')
