from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

# Create your tests here.


class LoginAndAccountTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='acc@test.com', password='pass1234')

    def test_login_signin_success_and_redirects_to_account(self):
        resp = self.client.post('/login/signin/', {'email': self.user.email, 'password': 'pass1234'})
        self.assertIn(resp.status_code, (302, 301))
        self.assertTrue(resp['Location'].endswith('/account/'))

    def test_login_signin_with_next_param(self):
        resp = self.client.post('/login/signin/?next=/checkout/', {'email': self.user.email, 'password': 'pass1234'})
        self.assertIn(resp.status_code, (302, 301))
        self.assertTrue(resp['Location'].endswith('/checkout/'))

    def test_login_signin_failure_shows_error(self):
        resp = self.client.post('/login/signin/', {'email': self.user.email, 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)


class AccountActionsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email='actions@test.com', password='pass1234')
        self.client.login(email=self.user.email, password='pass1234')

    def test_profile_update_name(self):
        resp = self.client.post('/account/', {
            'profile_submit': '1',
            'name': 'Иван Тест'
        })
        self.assertIn(resp.status_code, (302, 301))
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Иван Тест')

    def test_address_update(self):
        resp = self.client.post('/account/', {
            'address_submit': '1',
            'line1': 'Ленина 1',
            'line2': '',
            'city': 'Екатеринбург',
            'region': 'Свердловская',
            'postal_code': '620000',
            'phone': '+79990000000',
        })
        self.assertIn(resp.status_code, (302, 301))
        from apps.accounts.models import Address
        addr = Address.objects.get(user=self.user)
        self.assertEqual(addr.city, 'Екатеринбург')
        self.assertEqual(addr.line1, 'Ленина 1')

    def test_topup_increases_balance_and_creates_transaction(self):
        resp = self.client.post('/account/', {
            'topup_submit': '1',
            'amount': '100.50',
            'next': '/checkout/'
        })
        self.assertIn(resp.status_code, (302, 301))
        self.assertTrue(resp['Location'].endswith('/checkout/'))
        from apps.accounts.models import BalanceTransaction
        self.user.refresh_from_db()
        self.assertEqual(str(self.user.balance), '100.50')
        self.assertTrue(BalanceTransaction.objects.filter(user=self.user, amount='100.50', type='credit').exists())

    def test_garage_add_and_delete(self):
        # Add vehicle
        resp = self.client.post('/account/garage/add/', {
            'make': 'Lada', 'model': 'Vesta', 'year': '', 'vin': ''
        })
        self.assertIn(resp.status_code, (302, 301))
        from apps.accounts.models import GarageVehicle
        self.assertEqual(GarageVehicle.objects.filter(user=self.user).count(), 1)
        gv = GarageVehicle.objects.get(user=self.user)
        # Delete vehicle
        resp = self.client.post(f'/account/garage/{gv.id}/delete/')
        self.assertIn(resp.status_code, (302, 301))
        self.assertEqual(GarageVehicle.objects.filter(user=self.user).count(), 0)

    def test_account_home_redirects_to_step2_when_names_missing(self):
        self.client.login(email=self.user.email, password='pass1234')
        resp = self.client.get('/account/')
        self.assertIn(resp.status_code, (302, 301))
        self.assertTrue(resp['Location'].endswith('/register/step2/'))

    def test_account_home_redirects_to_step3_when_address_missing(self):
        # Fill names
        self.user.first_name = 'Ivan'
        self.user.last_name = 'Petrov'
        self.user.save()
        self.client.login(email=self.user.email, password='pass1234')
        resp = self.client.get('/account/')
        self.assertIn(resp.status_code, (302, 301))
        self.assertTrue(resp['Location'].endswith('/register/step3/'))

    def test_account_home_redirects_to_step4_when_no_garage(self):
        # Fill names and minimal address
        from apps.accounts.models import Address
        self.user.first_name = 'Ivan'
        self.user.last_name = 'Petrov'
        self.user.save()
        Address.objects.create(user=self.user, city='Moscow', line1='Tverskaya 1', phone='+79990000000')
        self.client.login(email=self.user.email, password='pass1234')
        resp = self.client.get('/account/')
        self.assertIn(resp.status_code, (302, 301))
        self.assertTrue(resp['Location'].endswith('/register/step4/'))

    def test_account_home_opens_when_registration_complete(self):
        # Fill names, address and at least one car
        from apps.accounts.models import Address, GarageVehicle
        self.user.first_name = 'Ivan'
        self.user.last_name = 'Petrov'
        self.user.save()
        Address.objects.create(user=self.user, city='Moscow', line1='Tverskaya 1', phone='+79990000000')
        GarageVehicle.objects.create(user=self.user, make='Lada', model='Vesta')
        self.client.login(email=self.user.email, password='pass1234')
        resp = self.client.get('/account/')
        self.assertEqual(resp.status_code, 200)


class RegistrationFlowTests(TestCase):
    def test_registration_full_flow_success(self):
        resp = self.client.get('/register/')
        self.assertIn(resp.status_code, (302, 301))
        # Step 1: email + password
        data1 = {
            'email': 'newuser@example.com',
            'password': 'pass1234',
            'password2': 'pass1234',
        }
        resp = self.client.post('/register/step1/', data1)
        self.assertIn(resp.status_code, (302, 301))
        self.assertTrue(get_user_model().objects.filter(email='newuser@example.com').exists())
        # Step 2: profile + phone
        data2 = {
            'first_name': 'Ivan',
            'last_name': 'Petrov',
            'phone': '+79991234567',
        }
        resp = self.client.post('/register/step2/', data2)
        self.assertIn(resp.status_code, (302, 301))
        # Step 3: address (with phone field present and required)
        data3 = {
            'city': 'Moscow',
            'line1': 'Tverskaya 1',
            'line2': '',
            'region': 'Moscow',
            'postal_code': '101000',
            'phone': '+79991234567',
        }
        resp = self.client.post('/register/step3/', data3)
        self.assertIn(resp.status_code, (302, 301))
        # Step 4: garage vehicle
        data4 = {
            'make': 'Lada',
            'model': 'Vesta',
            'year': '',
            'vin': '',
        }
        resp = self.client.post('/register/step4/', data4)
        self.assertIn(resp.status_code, (302, 301))
        # Should land in account without further registration redirects
        resp = self.client.get('/account/')
        self.assertEqual(resp.status_code, 200)

    def test_step4_validation_missing_make_model(self):
        # Prepare steps 1-3 quickly
        self.client.post('/register/step1/', {
            'email': 'u2@example.com', 'password': 'pass1234', 'password2': 'pass1234'
        })
        self.client.post('/register/step2/', {
            'first_name': 'Petr', 'last_name': 'Ivanov', 'phone': '+79990000000'
        })
        self.client.post('/register/step3/', {
            'city': 'SPB', 'line1': 'Nevsky 1', 'line2': '', 'region': 'SPB', 'postal_code': '190000', 'phone': '+79990000000'
        })
        # Step 4: submit missing fields to trigger errors
        resp = self.client.post('/register/step4/', {
            'make': '', 'model': '', 'year': '', 'vin': ''
        })
        # Should not redirect, should re-render with errors
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Марка')
        self.assertContains(resp, 'Модель')

    def test_anon_cannot_skip_to_later_steps(self):
        resp = self.client.get('/register/step2/')
        self.assertIn(resp.status_code, (302, 301))
        resp = self.client.get('/register/step3/')
        self.assertIn(resp.status_code, (302, 301))
        resp = self.client.get('/register/step4/')
        self.assertIn(resp.status_code, (302, 301))

# Create your tests here.
