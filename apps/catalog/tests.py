from django.test import TestCase
from decimal import Decimal

from .models import Category, Product


class CatalogSiteTests(TestCase):
    def setUp(self):
        self.cat1 = Category.objects.create(name="Электрика", slug="elektrika")
        self.cat2 = Category.objects.create(name="Двигатель", slug="dvigatel")
        self.p1 = Product.objects.create(
            name="Аккумулятор Bosch 104",
            slug="bosch-104-akb-1004",
            sku="AKB-1004",
            description="Акк для авто",
            manufacturer="Bosch",
            price=Decimal("4213.00"),
            in_stock=10,
            images=["https://example.com/img.jpg"],
            category=self.cat1,
        )
        self.p2 = Product.objects.create(
            name="Свеча зажигания NGK",
            slug="svetcha-ngk-001",
            sku="NGK-001",
            description="Свеча",
            manufacturer="NGK",
            price=Decimal("300.00"),
            in_stock=0,
            images=["https://example.com/img2.jpg"],
            category=self.cat2,
        )

    def test_catalog_list_page_loads(self):
        resp = self.client.get('/catalog/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.p1.name)
        self.assertContains(resp, self.p2.name)

    def test_catalog_filters_and_search(self):
        # Search by manufacturer (case-insensitive)
        resp = self.client.get('/catalog/?search=bosch')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.p1.name)
        # Category filter
        resp = self.client.get('/catalog/?category=elektrika')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.p1.name)
        # Price filter
        resp = self.client.get('/catalog/?price_max=400')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.p2.name)
        # In stock filter
        resp = self.client.get('/catalog/?in_stock=1')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.p1.name)

    def test_catalog_goto_redirects_to_single_product(self):
        # Filter to a single item and use goto=1
        resp = self.client.get('/catalog/?search=ngk&goto=1')
        self.assertIn(resp.status_code, (302, 301))
        self.assertTrue(resp['Location'].endswith(f'/parts/{self.p2.slug}/'))

    def test_product_detail_page(self):
        resp = self.client.get(f'/parts/{self.p1.slug}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.p1.name)
