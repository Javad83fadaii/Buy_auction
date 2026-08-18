import shutil
import tempfile
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DataError, IntegrityError, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from PIL import Image

from .choices import ContactMethodChoices, ProductSourceTypeChoices, ProductStatusChoices
from .models import Product, ProductImage

User = get_user_model()
PRODUCT_TEST_MEDIA_ROOT = tempfile.mkdtemp()
CONSTRAINT_TEST_MEDIA_ROOT = tempfile.mkdtemp()


def create_test_image_file(name: str = 'test.png', image_format: str = 'PNG') -> SimpleUploadedFile:
    file_object = BytesIO()
    image = Image.new('RGB', (20, 20), color='white')
    image.save(file_object, format=image_format)
    file_object.seek(0)
    return SimpleUploadedFile(name, file_object.read(), content_type='image/png')


@override_settings(MEDIA_ROOT=PRODUCT_TEST_MEDIA_ROOT)
class ProductModelTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PRODUCT_TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='operator', password='StrongPass123!')

    def create_product(self, **extra_fields) -> Product:
        data = {
            'title': 'تابلوی نمونه',
            'product_code': 'MAN-1001',
            'suggested_price': Decimal('1250000.00'),
            'suitable_price': Decimal('1350000.00'),
            'artist': 'هنرمند نمونه',
            'suggested_by': 'علی رضایی',
            'contact_method': ContactMethodChoices.WHATSAPP,
            'created_by': self.user,
            'updated_by': self.user,
        }
        data.update(extra_fields)
        return Product.objects.create(**data)

    def test_create_product(self):
        product = self.create_product()

        self.assertEqual(product.source_type, ProductSourceTypeChoices.MANUAL)
        self.assertEqual(product.status, ProductStatusChoices.DRAFT)
        self.assertEqual(product.created_by, self.user)
        self.assertIsNotNone(product.created_at)
        self.assertIsNotNone(product.updated_at)

    def test_required_title(self):
        product = Product(created_by=self.user)

        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_decimal_prices_are_preserved(self):
        product = self.create_product(
            suggested_price=Decimal('9999999999999999.99'),
            suitable_price=Decimal('2500000.50'),
        )

        self.assertEqual(product.suggested_price, Decimal('9999999999999999.99'))
        self.assertEqual(product.suitable_price, Decimal('2500000.50'))

    def test_negative_price_validation(self):
        product = Product(
            title='اثر نامعتبر',
            suggested_price=Decimal('-1'),
            created_by=self.user,
        )

        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_source_type_can_be_changed_for_future_sources(self):
        product = self.create_product(source_type=ProductSourceTypeChoices.CHRISTIES)

        self.assertEqual(product.source_type, ProductSourceTypeChoices.CHRISTIES)

    def test_status_can_be_set(self):
        product = self.create_product(status=ProductStatusChoices.PENDING_REVIEW)

        self.assertEqual(product.status, ProductStatusChoices.PENDING_REVIEW)

    def test_updated_at_changes_on_update(self):
        product = self.create_product()
        original_updated_at = product.updated_at

        product.title = 'عنوان ویرایش‌شده'
        product.save(update_fields=['title', 'updated_at'])
        product.refresh_from_db()

        self.assertGreaterEqual(product.updated_at, original_updated_at)

    def test_product_code_can_repeat_across_different_sources(self):
        self.create_product(product_code='SRC-101', source_type=ProductSourceTypeChoices.MANUAL)
        duplicate_other_source = self.create_product(
            product_code='SRC-101',
            source_type=ProductSourceTypeChoices.CHRISTIES,
            title='اثر منبع دیگر',
        )

        self.assertEqual(duplicate_other_source.product_code, 'SRC-101')

    def test_blank_product_code_is_normalized_to_none(self):
        first_product = self.create_product(product_code='   ', title='اثر اول')
        second_product = self.create_product(product_code='', title='اثر دوم')

        self.assertIsNone(first_product.product_code)
        self.assertIsNone(second_product.product_code)

    def test_deleting_creator_keeps_product_history(self):
        product = self.create_product()
        self.user.delete()
        product.refresh_from_db()

        self.assertIsNone(product.created_by)
        self.assertIsNone(product.updated_by)

    def test_product_image_creation_and_relation(self):
        product = self.create_product()
        image = ProductImage.objects.create(
            product=product,
            image=create_test_image_file(),
            is_primary=True,
            sort_order=1,
        )

        self.assertEqual(image.product, product)
        self.assertEqual(product.images.count(), 1)
        self.assertTrue(image.is_primary)

    def test_product_image_rejects_invalid_file_type(self):
        product = self.create_product()
        image = ProductImage(
            product=product,
            image=SimpleUploadedFile('document.txt', b'invalid', content_type='text/plain'),
        )

        with self.assertRaises(ValidationError):
            image.full_clean()

    def test_product_image_primary_validation(self):
        product = self.create_product()
        ProductImage.objects.create(
            product=product,
            image=create_test_image_file(name='first.png'),
            is_primary=True,
        )
        second_image = ProductImage(
            product=product,
            image=create_test_image_file(name='second.png'),
            is_primary=True,
        )

        with self.assertRaises(ValidationError):
            second_image.full_clean()

    def test_product_image_sort_order_validation(self):
        product = self.create_product()
        image = ProductImage(
            product=product,
            image=create_test_image_file(),
            sort_order=-1,
        )

        with self.assertRaises(ValidationError):
            image.full_clean()

    def test_product_image_upload_path_uses_product_id_directory(self):
        product = self.create_product()
        image = ProductImage.objects.create(
            product=product,
            image=create_test_image_file(name='sample.png'),
        )

        self.assertTrue(image.image.name.startswith(f'products/{product.id}/'))


@override_settings(MEDIA_ROOT=CONSTRAINT_TEST_MEDIA_ROOT)
class ProductConstraintTests(TransactionTestCase):
    reset_sequences = True

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(CONSTRAINT_TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='constraint_user', password='StrongPass123!')

    def create_product(self, **extra_fields) -> Product:
        data = {
            'title': 'Constraint Product',
            'product_code': 'UNQ-100',
            'created_by': self.user,
        }
        data.update(extra_fields)
        return Product.objects.create(**data)

    def test_product_code_is_unique_per_source(self):
        self.create_product()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_product(title='Duplicate Product')

    def test_database_rejects_negative_suggested_price(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(
                    title='Negative Price',
                    suggested_price=Decimal('-10.00'),
                    created_by=self.user,
                )

    def test_database_rejects_negative_sort_order(self):
        product = self.create_product(product_code='IMG-001')

        with self.assertRaises((IntegrityError, DataError)):
            with transaction.atomic():
                ProductImage.objects.create(
                    product=product,
                    image=create_test_image_file(),
                    sort_order=-1,
                )

    def test_multiple_null_product_codes_are_allowed(self):
        self.create_product(product_code=None, title='Null Code 1')
        second_product = self.create_product(product_code=None, title='Null Code 2')

        self.assertIsNone(second_product.product_code)
