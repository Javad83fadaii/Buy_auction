import shutil
import tempfile
from io import BytesIO
from urllib.parse import quote, urlencode
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from accounts.constants import ADMIN_ROLE, OPERATOR_ROLE, VIEWER_ROLE
from accounts.services import ensure_default_roles
from .choices import ContactMethodChoices, ProductSourceTypeChoices, ProductStatusChoices
from .forms import ProductCreateForm
from .models import Product, ProductImage
from .validators import MAX_PRODUCT_IMAGE_SIZE

User = get_user_model()


class ProductCreateBaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_media_root = tempfile.mkdtemp()
        cls.media_override = override_settings(MEDIA_ROOT=cls.temp_media_root)
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        shutil.rmtree(cls.temp_media_root, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        ensure_default_roles()
        cls.password = 'StrongPass123!'
        cls.admin_group = Group.objects.get(name=ADMIN_ROLE)
        cls.operator_group = Group.objects.get(name=OPERATOR_ROLE)
        cls.viewer_group = Group.objects.get(name=VIEWER_ROLE)

        cls.admin_user = cls.create_user('product_admin', cls.admin_group)
        cls.operator_user = cls.create_user('product_operator', cls.operator_group)
        cls.viewer_user = cls.create_user('product_viewer', cls.viewer_group)

    @classmethod
    def create_user(cls, username, group):
        user = User.objects.create_user(
            username=username,
            password=cls.password,
            email=f'{username}@example.com',
        )
        user.groups.add(group)
        user.refresh_from_db()
        return user

    def create_test_image(self, name='test-image.jpg', size=(40, 40), color='blue'):
        image_bytes = BytesIO()
        image = Image.new('RGB', size, color=color)
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        return SimpleUploadedFile(name, image_bytes.getvalue(), content_type='image/jpeg')

    def get_valid_payload(self, **overrides):
        payload = {
            'suggested_by': 'علی رضایی',
            'contact_method': ContactMethodChoices.PHONE,
            'suggestion_date': '2026-08-19',
            'title': 'تابلوی شماره یک',
            'product_code': 'ART-100',
            'description': 'توضیح نمونه',
            'artist': 'هنرمند نمونه',
            'production_date': '2024-05-01',
            'production_location': 'تهران',
            'material': 'رنگ روغن',
            'subject': 'منظره',
            'usage': 'تزئینی',
            'art_type': 'نقاشی',
            'suggested_price': '2500000.50',
            'suitable_price': '2200000',
            'is_cancelled': '',
            'is_notable': 'on',
            'needs_expert_review': 'on',
        }
        payload.update(overrides)
        return payload

    def build_form(self, *, data=None, images=None):
        files = MultiValueDict({'images': images or [self.create_test_image()]})
        return ProductCreateForm(data=data or self.get_valid_payload(), files=files)

    def create_product(self, **overrides):
        payload = {
            'title': 'اثر تستی',
            'product_code': 'ART-DEFAULT',
            'artist': 'هنرمند تستی',
            'art_type': 'نقاشی',
            'suitable_price': '1500000',
            'source_type': ProductSourceTypeChoices.MANUAL,
            'status': ProductStatusChoices.DRAFT,
        }
        payload.update(overrides)
        product = Product.objects.create(**payload)
        return product


class ProductCreatePermissionTests(ProductCreateBaseTestCase):
    def test_anonymous_cannot_access_create_page(self):
        response = self.client.get(reverse('products:create'))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('products:create')}",
        )

    def test_viewer_cannot_access_create_page(self):
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse('products:create'))

        self.assertEqual(response.status_code, 403)

    def test_operator_can_access_create_page(self):
        self.client.force_login(self.operator_user)

        response = self.client.get(reverse('products:create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ثبت پیشنهاد جدید')

    def test_admin_can_access_create_page(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse('products:create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ثبت پیشنهاد جدید')


class ProductCreateFormTests(ProductCreateBaseTestCase):
    def test_valid_form(self):
        form = self.build_form()

        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = self.build_form(data=self.get_valid_payload(title=''))

        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_invalid_price(self):
        form = self.build_form(data=self.get_valid_payload(suggested_price='invalid-price'))

        self.assertFalse(form.is_valid())
        self.assertIn('suggested_price', form.errors)

    def test_negative_price(self):
        form = self.build_form(data=self.get_valid_payload(suggested_price='-1'))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['suggested_price'][0], 'قیمت نمی‌تواند منفی باشد.')

    def test_invalid_contact_method(self):
        form = self.build_form(data=self.get_valid_payload(contact_method='INVALID'))

        self.assertFalse(form.is_valid())
        self.assertIn('contact_method', form.errors)

    def test_invalid_product_code(self):
        Product.objects.create(
            title='اثر قبلی',
            product_code='ART-100',
            source_type=ProductSourceTypeChoices.MANUAL,
            status=ProductStatusChoices.DRAFT,
        )

        form = self.build_form(data=self.get_valid_payload(product_code='  ART-100  '))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['product_code'][0], 'این کد اثر قبلاً برای پیشنهاد دستی ثبت شده است.')


class ProductCreateFlowTests(ProductCreateBaseTestCase):
    def post_create(self, *, user=None, data=None, images=None, follow=False):
        self.client.force_login(user or self.operator_user)
        return self.client.post(
            reverse('products:create'),
            data={**(data or self.get_valid_payload()), 'images': images or [self.create_test_image()]},
            follow=follow,
        )

    def test_product_created_successfully(self):
        response = self.post_create(follow=True)

        self.assertRedirects(response, reverse('products:create'))
        self.assertContains(response, 'اثر با موفقیت ثبت شد.')
        self.assertEqual(Product.objects.count(), 1)

    def test_created_by_is_correct(self):
        self.post_create()

        product = Product.objects.get()
        self.assertEqual(product.created_by, self.operator_user)

    def test_updated_by_is_correct(self):
        self.post_create()

        product = Product.objects.get()
        self.assertEqual(product.updated_by, self.operator_user)

    def test_source_type_is_manual(self):
        self.post_create(data=self.get_valid_payload())

        product = Product.objects.get()
        self.assertEqual(product.source_type, ProductSourceTypeChoices.MANUAL)

    def test_status_is_draft(self):
        self.post_create(data=self.get_valid_payload())

        product = Product.objects.get()
        self.assertEqual(product.status, ProductStatusChoices.DRAFT)

    def test_product_code_blank_is_saved_as_null(self):
        self.post_create(data=self.get_valid_payload(product_code='   '))

        product = Product.objects.get()
        self.assertIsNone(product.product_code)

    def test_one_image_is_created(self):
        self.post_create(images=[self.create_test_image()])

        self.assertEqual(ProductImage.objects.count(), 1)

    def test_multiple_images_are_created(self):
        self.post_create(images=[self.create_test_image('one.jpg'), self.create_test_image('two.jpg')])

        self.assertEqual(ProductImage.objects.count(), 2)

    def test_first_image_becomes_primary(self):
        self.post_create(images=[self.create_test_image('one.jpg'), self.create_test_image('two.jpg')])

        images = list(ProductImage.objects.order_by('sort_order'))
        self.assertTrue(images[0].is_primary)
        self.assertFalse(images[1].is_primary)

    def test_sort_order_matches_upload_order(self):
        self.post_create(
            images=[
                self.create_test_image('first.jpg'),
                self.create_test_image('second.jpg'),
                self.create_test_image('third.jpg'),
            ]
        )

        self.assertEqual(list(ProductImage.objects.values_list('sort_order', flat=True)), [0, 1, 2])

    def test_invalid_image_is_rejected(self):
        invalid_file = SimpleUploadedFile('invalid.txt', b'not-an-image', content_type='text/plain')

        response = self.post_create(images=[invalid_file])

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'فرمت تصویر مجاز نیست.')
        self.assertEqual(Product.objects.count(), 0)

    def test_image_over_5mb_is_rejected(self):
        large_file = SimpleUploadedFile(
            'large.jpg',
            b'a' * (MAX_PRODUCT_IMAGE_SIZE + 1),
            content_type='image/jpeg',
        )

        response = self.post_create(images=[large_file])

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'حجم تصویر نباید بیشتر از 5 مگابایت باشد.')
        self.assertEqual(Product.objects.count(), 0)

    def test_transaction_rolls_back_when_image_save_fails(self):
        original_full_clean = ProductImage.full_clean
        call_count = {'value': 0}

        def failing_full_clean(instance, *args, **kwargs):
            call_count['value'] += 1
            if call_count['value'] == 2:
                raise ValidationError({'image': 'خطا در اعتبارسنجی تصویر دوم.'})
            return original_full_clean(instance, *args, **kwargs)

        with patch('products.services.ProductImage.full_clean', new=failing_full_clean):
            response = self.post_create(
                images=[self.create_test_image('one.jpg'), self.create_test_image('two.jpg')]
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'خطا در اعتبارسنجی تصویر دوم.')
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(ProductImage.objects.count(), 0)


class ProductListViewTests(ProductCreateBaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.view_product_permission = Permission.objects.get(codename='view_product')
        cls.authorized_user = cls.create_user('product_list_user', cls.viewer_group)
        cls.authorized_user.user_permissions.add(cls.view_product_permission)

    def get_list(self, *, user=None, page=None, q=None):
        if user is not None:
            self.client.force_login(user)

        url = reverse('products:list')
        query_params = {}
        if q is not None:
            query_params['q'] = q
        if page:
            query_params['page'] = page
        if query_params:
            url = f'{url}?{urlencode(query_params)}'

        return self.client.get(url)

    def test_anonymous_cannot_access_product_list(self):
        response = self.get_list()

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('products:list')}",
        )

    def test_authorized_user_can_view_product_list(self):
        response = self.get_list(user=self.authorized_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'لیست محصولات')

    def test_products_are_displayed(self):
        product = self.create_product(title='اثر نمایشی', product_code='ART-DISPLAY')

        response = self.get_list(user=self.authorized_user)

        self.assertContains(response, product.title)
        self.assertContains(response, product.product_code)

    def test_pagination_shows_twenty_products_per_page(self):
        for index in range(21):
            self.create_product(
                title=f'اثر {index}',
                product_code=f'ART-{index}',
            )

        first_page_response = self.get_list(user=self.authorized_user)
        second_page_response = self.get_list(user=self.authorized_user, page=2)

        self.assertEqual(len(first_page_response.context['products']), 20)
        self.assertTrue(first_page_response.context['is_paginated'])
        self.assertContains(first_page_response, 'صفحه 1 از 2')
        self.assertEqual(len(second_page_response.context['products']), 1)

    def test_primary_image_is_displayed(self):
        product = self.create_product()
        primary_image = ProductImage.objects.create(
            product=product,
            image=self.create_test_image('primary.jpg'),
            is_primary=True,
            sort_order=0,
        )
        ProductImage.objects.create(
            product=product,
            image=self.create_test_image('secondary.jpg'),
            is_primary=False,
            sort_order=1,
        )

        response = self.get_list(user=self.authorized_user)

        self.assertContains(response, primary_image.image.url)
        self.assertEqual(response.context['products'][0].primary_images[0].pk, primary_image.pk)

    def test_empty_state_is_displayed_when_no_product_exists(self):
        response = self.get_list(user=self.authorized_user)

        self.assertContains(response, 'هنوز محصولی ثبت نشده است.')

    def test_search_by_title(self):
        matching_product = self.create_product(title='تابلوی آبی', product_code='ART-TITLE-1')
        self.create_product(title='مجسمه سنگی', product_code='ART-TITLE-2')

        response = self.get_list(user=self.authorized_user, q='تابلوی')

        products = list(response.context['products'])
        self.assertEqual(products, [matching_product])
        self.assertContains(response, matching_product.title)
        self.assertNotContains(response, 'مجسمه سنگی')

    def test_search_by_product_code(self):
        matching_product = self.create_product(title='اثر اول', product_code='ART-CODE-77')
        self.create_product(title='اثر دوم', product_code='ART-CODE-88')

        response = self.get_list(user=self.authorized_user, q='code-77')

        self.assertEqual(list(response.context['products']), [matching_product])
        self.assertContains(response, matching_product.product_code)
        self.assertNotContains(response, 'ART-CODE-88')

    def test_search_by_artist(self):
        matching_product = self.create_product(title='اثر هنری', artist='ونگوگ', product_code='ART-ARTIST-1')
        self.create_product(title='اثر دیگر', artist='پیکاسو', product_code='ART-ARTIST-2')

        response = self.get_list(user=self.authorized_user, q='ونگو')

        self.assertEqual(list(response.context['products']), [matching_product])
        self.assertContains(response, matching_product.artist)
        self.assertNotContains(response, 'پیکاسو')

    def test_search_by_suggested_by(self):
        matching_product = self.create_product(
            title='اثر پیشنهادی',
            product_code='ART-SUGGEST-1',
            suggested_by='سارا احمدی',
        )
        self.create_product(
            title='اثر غیرمرتبط',
            product_code='ART-SUGGEST-2',
            suggested_by='مهدی کریمی',
        )

        response = self.get_list(user=self.authorized_user, q='سارا')

        self.assertEqual(list(response.context['products']), [matching_product])
        self.assertContains(response, matching_product.title)
        self.assertNotContains(response, 'اثر غیرمرتبط')

    def test_search_is_case_insensitive(self):
        matching_product = self.create_product(title='Sunset', product_code='ART-CASE-1')
        self.create_product(title='Moonlight', product_code='ART-CASE-2')

        response = self.get_list(user=self.authorized_user, q='sunSET')

        self.assertEqual(list(response.context['products']), [matching_product])
        self.assertContains(response, matching_product.title)
        self.assertNotContains(response, 'Moonlight')

    def test_empty_search_returns_all_products(self):
        first_product = self.create_product(title='اثر اول', product_code='ART-EMPTY-1')
        second_product = self.create_product(title='اثر دوم', product_code='ART-EMPTY-2')

        response = self.get_list(user=self.authorized_user, q='   ')

        self.assertContains(response, first_product.title)
        self.assertContains(response, second_product.title)
        self.assertEqual(response.context['search_query'], '')

    def test_no_result_search_displays_message(self):
        self.create_product(title='اثر موجود', product_code='ART-NO-RESULT')

        response = self.get_list(user=self.authorized_user, q='ناموجود')

        self.assertContains(response, 'محصولی مطابق جستجوی شما پیدا نشد.')
        self.assertEqual(len(response.context['products']), 0)
        self.assertContains(response, 'value="ناموجود"', html=False)

    def test_search_works_with_pagination(self):
        for index in range(21):
            self.create_product(
                title=f'محصول مشترک {index}',
                product_code=f'SHARED-{index}',
            )
        self.create_product(title='محصول نامرتبط', product_code='OTHER-1')

        first_page_response = self.get_list(user=self.authorized_user, q='مشترک')
        second_page_response = self.get_list(user=self.authorized_user, q='مشترک', page=2)

        self.assertEqual(len(first_page_response.context['products']), 20)
        self.assertTrue(first_page_response.context['is_paginated'])
        self.assertContains(first_page_response, '?q=%D9%85%D8%B4%D8%AA%D8%B1%DA%A9&amp;page=2', html=False)
        self.assertEqual(len(second_page_response.context['products']), 1)
        self.assertContains(second_page_response, 'value="مشترک"', html=False)
        self.assertNotContains(first_page_response, 'محصول نامرتبط')

    def test_anonymous_access_remains_restricted_when_searching(self):
        response = self.get_list(q='اثر')
        expected_next = quote(f"{reverse('products:list')}?{urlencode({'q': 'اثر'})}")

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={expected_next}",
        )
