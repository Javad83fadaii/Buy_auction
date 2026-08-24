import shutil
import tempfile
from datetime import date, timedelta
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
from django.utils import timezone

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

    def get_list(
        self,
        *,
        user=None,
        page=None,
        q=None,
        status=None,
        source=None,
        art_type=None,
        date_from=None,
        date_to=None,
        sort=None,
    ):
        if user is not None:
            self.client.force_login(user)

        url = reverse('products:list')
        query_params = {}
        if q is not None:
            query_params['q'] = q
        if status is not None:
            query_params['status'] = status
        if source is not None:
            query_params['source'] = source
        if art_type is not None:
            query_params['art_type'] = art_type
        if date_from is not None:
            query_params['date_from'] = date_from
        if date_to is not None:
            query_params['date_to'] = date_to
        if sort is not None:
            query_params['sort'] = sort
        if page:
            query_params['page'] = page
        if query_params:
            url = f'{url}?{urlencode(query_params)}'

        return self.client.get(url)

    def set_created_at(self, product, created_at):
        Product.objects.filter(pk=product.pk).update(created_at=created_at)
        product.refresh_from_db()
        return product

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

    def test_filter_by_draft_status(self):
        matching_product = self.create_product(
            title='اثر پیش‌نویس',
            product_code='ART-STATUS-DRAFT',
            status=ProductStatusChoices.DRAFT,
        )
        self.create_product(
            title='اثر منتشرشده',
            product_code='ART-STATUS-PUBLISHED',
            status=ProductStatusChoices.PUBLISHED,
        )

        response = self.get_list(user=self.authorized_user, status=ProductStatusChoices.DRAFT)

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_filter_by_pending_review_status(self):
        matching_product = self.create_product(
            title='اثر در انتظار بررسی',
            product_code='ART-STATUS-PENDING',
            status=ProductStatusChoices.PENDING_REVIEW,
        )
        self.create_product(
            title='اثر ردشده',
            product_code='ART-STATUS-REJECTED',
            status=ProductStatusChoices.REJECTED,
        )

        response = self.get_list(user=self.authorized_user, status=ProductStatusChoices.PENDING_REVIEW)

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_filter_by_approved_status(self):
        matching_product = self.create_product(
            title='اثر تاییدشده',
            product_code='ART-STATUS-APPROVED',
            status=ProductStatusChoices.APPROVED,
        )
        self.create_product(
            title='اثر پیش‌نویس دوم',
            product_code='ART-STATUS-DRAFT-2',
            status=ProductStatusChoices.DRAFT,
        )

        response = self.get_list(user=self.authorized_user, status=ProductStatusChoices.APPROVED)

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_filter_by_published_status(self):
        matching_product = self.create_product(
            title='اثر منتشرشده',
            product_code='ART-STATUS-PUBLISHED-2',
            status=ProductStatusChoices.PUBLISHED,
        )
        self.create_product(
            title='اثر تاییدشده دوم',
            product_code='ART-STATUS-APPROVED-2',
            status=ProductStatusChoices.APPROVED,
        )

        response = self.get_list(user=self.authorized_user, status=ProductStatusChoices.PUBLISHED)

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_filter_by_rejected_status(self):
        matching_product = self.create_product(
            title='اثر ردشده',
            product_code='ART-STATUS-REJECTED-2',
            status=ProductStatusChoices.REJECTED,
        )
        self.create_product(
            title='اثر منتشرنشده',
            product_code='ART-STATUS-DRAFT-3',
            status=ProductStatusChoices.DRAFT,
        )

        response = self.get_list(user=self.authorized_user, status=ProductStatusChoices.REJECTED)

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_filter_by_manual_source(self):
        matching_product = self.create_product(
            title='اثر دستی',
            product_code='ART-SOURCE-MANUAL',
            source_type=ProductSourceTypeChoices.MANUAL,
        )
        self.create_product(
            title='اثر کریستیز',
            product_code='ART-SOURCE-CHRISTIES',
            source_type=ProductSourceTypeChoices.CHRISTIES,
        )

        response = self.get_list(user=self.authorized_user, source=ProductSourceTypeChoices.MANUAL)

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_filter_by_christies_source(self):
        matching_product = self.create_product(
            title='اثر کریستیز',
            product_code='ART-SOURCE-CHRISTIES-2',
            source_type=ProductSourceTypeChoices.CHRISTIES,
        )
        self.create_product(
            title='اثر ساتبیز',
            product_code='ART-SOURCE-SOTHEBYS',
            source_type=ProductSourceTypeChoices.SOTHEBYS,
        )

        response = self.get_list(user=self.authorized_user, source=ProductSourceTypeChoices.CHRISTIES)

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_filter_by_sothebys_source(self):
        matching_product = self.create_product(
            title='اثر ساتبیز',
            product_code='ART-SOURCE-SOTHEBYS-2',
            source_type=ProductSourceTypeChoices.SOTHEBYS,
        )
        self.create_product(
            title='اثر سایر حراجی‌ها',
            product_code='ART-SOURCE-OTHER',
            source_type=ProductSourceTypeChoices.OTHER_AUCTION,
        )

        response = self.get_list(user=self.authorized_user, source=ProductSourceTypeChoices.SOTHEBYS)

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_filter_by_other_auction_source(self):
        matching_product = self.create_product(
            title='اثر سایر حراجی‌ها',
            product_code='ART-SOURCE-OTHER-2',
            source_type=ProductSourceTypeChoices.OTHER_AUCTION,
        )
        self.create_product(
            title='اثر دستی دوم',
            product_code='ART-SOURCE-MANUAL-2',
            source_type=ProductSourceTypeChoices.MANUAL,
        )

        response = self.get_list(user=self.authorized_user, source=ProductSourceTypeChoices.OTHER_AUCTION)

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_filter_by_art_type(self):
        matching_product = self.create_product(
            title='اثر نقاشی',
            product_code='ART-TYPE-PAINTING',
            art_type='painting',
        )
        self.create_product(
            title='اثر مجسمه',
            product_code='ART-TYPE-SCULPTURE',
            art_type='sculpture',
        )

        response = self.get_list(user=self.authorized_user, art_type='painting')

        self.assertEqual(list(response.context['products']), [matching_product])
        self.assertContains(response, '<option value="painting" selected>', html=False)

    def test_invalid_art_type_returns_no_results(self):
        self.create_product(
            title='اثر موجود',
            product_code='ART-TYPE-EXISTING',
            art_type='painting',
        )

        response = self.get_list(user=self.authorized_user, art_type='invalid-art-type')

        self.assertEqual(len(response.context['products']), 0)
        self.assertContains(response, 'محصولی مطابق فیلترها یا جستجوی شما پیدا نشد.')

    def test_filter_by_date_from(self):
        self.create_product(
            title='اثر قدیمی',
            product_code='ART-DATE-FROM-OLD',
            suggestion_date=date(2026, 1, 1),
        )
        matching_product = self.create_product(
            title='اثر جدید',
            product_code='ART-DATE-FROM-NEW',
            suggestion_date=date(2026, 3, 1),
        )

        response = self.get_list(user=self.authorized_user, date_from='2026-02-01')

        self.assertEqual(list(response.context['products']), [matching_product])
        self.assertContains(response, 'value="2026-02-01"', html=False)

    def test_filter_by_date_to(self):
        matching_product = self.create_product(
            title='اثر قدیمی',
            product_code='ART-DATE-TO-OLD',
            suggestion_date=date(2026, 2, 1),
        )
        self.create_product(
            title='اثر جدید',
            product_code='ART-DATE-TO-NEW',
            suggestion_date=date(2026, 5, 1),
        )

        response = self.get_list(user=self.authorized_user, date_to='2026-03-01')

        self.assertEqual(list(response.context['products']), [matching_product])
        self.assertContains(response, 'value="2026-03-01"', html=False)

    def test_filter_by_date_range(self):
        self.create_product(
            title='اثر خارج از بازه اول',
            product_code='ART-DATE-RANGE-1',
            suggestion_date=date(2026, 1, 1),
        )
        first_matching_product = self.create_product(
            title='اثر داخل بازه اول',
            product_code='ART-DATE-RANGE-2',
            suggestion_date=date(2026, 3, 15),
        )
        second_matching_product = self.create_product(
            title='اثر داخل بازه دوم',
            product_code='ART-DATE-RANGE-3',
            suggestion_date=date(2026, 4, 10),
        )
        self.create_product(
            title='اثر خارج از بازه دوم',
            product_code='ART-DATE-RANGE-4',
            suggestion_date=date(2026, 6, 1),
        )

        response = self.get_list(
            user=self.authorized_user,
            date_from='2026-03-01',
            date_to='2026-04-30',
        )

        self.assertEqual(
            list(response.context['products']),
            [second_matching_product, first_matching_product],
        )

    def test_invalid_date_does_not_crash_and_shows_validation_error(self):
        matching_product = self.create_product(
            title='اثر موجود',
            product_code='ART-DATE-INVALID',
            suggestion_date=date(2026, 4, 1),
        )

        response = self.get_list(user=self.authorized_user, date_from='invalid-date')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['products']), [matching_product])
        self.assertEqual(response.context['filter_form'].errors['date_from'][0], 'تاریخ شروع معتبر نیست.')
        self.assertContains(response, 'تاریخ شروع معتبر نیست.')

    def test_empty_dates_do_not_apply_filter(self):
        first_product = self.create_product(title='اثر اول', product_code='ART-DATE-EMPTY-1')
        second_product = self.create_product(title='اثر دوم', product_code='ART-DATE-EMPTY-2')

        response = self.get_list(
            user=self.authorized_user,
            date_from='',
            date_to='',
        )

        self.assertContains(response, first_product.title)
        self.assertContains(response, second_product.title)
        self.assertEqual(response.context['filter_form'].cleaned_data['date_from'], None)
        self.assertEqual(response.context['filter_form'].cleaned_data['date_to'], None)

    def test_default_sort_is_newest_first(self):
        older_product = self.create_product(title='اثر قدیمی', product_code='ART-SORT-DEFAULT-1')
        newer_product = self.create_product(title='اثر جدید', product_code='ART-SORT-DEFAULT-2')
        now = timezone.now()
        self.set_created_at(older_product, now - timedelta(days=2))
        self.set_created_at(newer_product, now - timedelta(days=1))

        response = self.get_list(user=self.authorized_user)

        self.assertEqual(list(response.context['products']), [newer_product, older_product])

    def test_sort_by_oldest(self):
        older_product = self.create_product(title='اثر قدیمی', product_code='ART-SORT-OLDEST-1')
        newer_product = self.create_product(title='اثر جدید', product_code='ART-SORT-OLDEST-2')
        now = timezone.now()
        self.set_created_at(older_product, now - timedelta(days=2))
        self.set_created_at(newer_product, now - timedelta(days=1))

        response = self.get_list(user=self.authorized_user, sort='created_at')

        self.assertEqual(list(response.context['products']), [older_product, newer_product])

    def test_sort_by_title_ascending(self):
        first_product = self.create_product(title='Alpha', product_code='ART-SORT-TITLE-1')
        second_product = self.create_product(title='Beta', product_code='ART-SORT-TITLE-2')
        third_product = self.create_product(title='Gamma', product_code='ART-SORT-TITLE-3')

        response = self.get_list(user=self.authorized_user, sort='title')

        self.assertEqual(list(response.context['products']), [first_product, second_product, third_product])

    def test_sort_by_title_descending(self):
        first_product = self.create_product(title='Alpha', product_code='ART-SORT-TITLE-DESC-1')
        second_product = self.create_product(title='Beta', product_code='ART-SORT-TITLE-DESC-2')
        third_product = self.create_product(title='Gamma', product_code='ART-SORT-TITLE-DESC-3')

        response = self.get_list(user=self.authorized_user, sort='-title')

        self.assertEqual(list(response.context['products']), [third_product, second_product, first_product])

    def test_sort_by_suitable_price_ascending_puts_nulls_last(self):
        low_price_product = self.create_product(
            title='اثر ارزان',
            product_code='ART-SORT-PRICE-ASC-1',
            suitable_price='100',
        )
        high_price_product = self.create_product(
            title='اثر گران',
            product_code='ART-SORT-PRICE-ASC-2',
            suitable_price='300',
        )
        null_price_product = self.create_product(
            title='اثر بدون قیمت',
            product_code='ART-SORT-PRICE-ASC-3',
            suitable_price=None,
        )

        response = self.get_list(user=self.authorized_user, sort='suitable_price')

        self.assertEqual(
            list(response.context['products']),
            [low_price_product, high_price_product, null_price_product],
        )

    def test_sort_by_suitable_price_descending_puts_nulls_last(self):
        low_price_product = self.create_product(
            title='اثر ارزان',
            product_code='ART-SORT-PRICE-DESC-1',
            suitable_price='100',
        )
        high_price_product = self.create_product(
            title='اثر گران',
            product_code='ART-SORT-PRICE-DESC-2',
            suitable_price='300',
        )
        null_price_product = self.create_product(
            title='اثر بدون قیمت',
            product_code='ART-SORT-PRICE-DESC-3',
            suitable_price=None,
        )

        response = self.get_list(user=self.authorized_user, sort='-suitable_price')

        self.assertEqual(
            list(response.context['products']),
            [high_price_product, low_price_product, null_price_product],
        )

    def test_invalid_sort_uses_default_sort(self):
        older_product = self.create_product(title='اثر قدیمی', product_code='ART-SORT-INVALID-1')
        newer_product = self.create_product(title='اثر جدید', product_code='ART-SORT-INVALID-2')
        now = timezone.now()
        self.set_created_at(older_product, now - timedelta(days=2))
        self.set_created_at(newer_product, now - timedelta(days=1))

        response = self.get_list(user=self.authorized_user, sort='invalid-sort')

        self.assertEqual(list(response.context['products']), [newer_product, older_product])
        self.assertContains(response, '<option value="-created_at" selected>', html=False)

    def test_search_and_status_filter_work_together(self):
        matching_product = self.create_product(
            title='محمد و طبیعت',
            product_code='ART-COMBO-SEARCH-STATUS-1',
            status=ProductStatusChoices.DRAFT,
        )
        self.create_product(
            title='محمد و معماری',
            product_code='ART-COMBO-SEARCH-STATUS-2',
            status=ProductStatusChoices.PUBLISHED,
        )
        self.create_product(
            title='اثر دیگر',
            product_code='ART-COMBO-SEARCH-STATUS-3',
            status=ProductStatusChoices.DRAFT,
        )

        response = self.get_list(
            user=self.authorized_user,
            q='محمد',
            status=ProductStatusChoices.DRAFT,
        )

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_search_and_source_filter_work_together(self):
        matching_product = self.create_product(
            title='محمد و دریا',
            product_code='ART-COMBO-SEARCH-SOURCE-1',
            source_type=ProductSourceTypeChoices.MANUAL,
        )
        self.create_product(
            title='محمد و کوه',
            product_code='ART-COMBO-SEARCH-SOURCE-2',
            source_type=ProductSourceTypeChoices.CHRISTIES,
        )

        response = self.get_list(
            user=self.authorized_user,
            q='محمد',
            source=ProductSourceTypeChoices.MANUAL,
        )

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_status_and_source_filters_work_together(self):
        matching_product = self.create_product(
            title='اثر ترکیبی',
            product_code='ART-COMBO-STATUS-SOURCE-1',
            status=ProductStatusChoices.DRAFT,
            source_type=ProductSourceTypeChoices.MANUAL,
        )
        self.create_product(
            title='اثر با منبع متفاوت',
            product_code='ART-COMBO-STATUS-SOURCE-2',
            status=ProductStatusChoices.DRAFT,
            source_type=ProductSourceTypeChoices.CHRISTIES,
        )
        self.create_product(
            title='اثر با وضعیت متفاوت',
            product_code='ART-COMBO-STATUS-SOURCE-3',
            status=ProductStatusChoices.PUBLISHED,
            source_type=ProductSourceTypeChoices.MANUAL,
        )

        response = self.get_list(
            user=self.authorized_user,
            status=ProductStatusChoices.DRAFT,
            source=ProductSourceTypeChoices.MANUAL,
        )

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_search_status_source_and_art_type_work_together(self):
        matching_product = self.create_product(
            title='محمد در باغ',
            product_code='ART-COMBO-ALL-1',
            status=ProductStatusChoices.DRAFT,
            source_type=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
        )
        self.create_product(
            title='محمد در باغ',
            product_code='ART-COMBO-ALL-2',
            status=ProductStatusChoices.DRAFT,
            source_type=ProductSourceTypeChoices.MANUAL,
            art_type='sculpture',
        )
        self.create_product(
            title='محمد در باغ',
            product_code='ART-COMBO-ALL-3',
            status=ProductStatusChoices.PUBLISHED,
            source_type=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
        )

        response = self.get_list(
            user=self.authorized_user,
            q='محمد',
            status=ProductStatusChoices.DRAFT,
            source=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
        )

        self.assertEqual(list(response.context['products']), [matching_product])

    def test_search_filter_date_and_sort_work_together(self):
        first_matching_product = self.create_product(
            title='محمد Alpha',
            product_code='ART-COMBO-DATE-SORT-1',
            status=ProductStatusChoices.DRAFT,
            source_type=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
            suggestion_date=date(2026, 3, 10),
        )
        second_matching_product = self.create_product(
            title='محمد Beta',
            product_code='ART-COMBO-DATE-SORT-2',
            status=ProductStatusChoices.DRAFT,
            source_type=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
            suggestion_date=date(2026, 3, 20),
        )
        self.create_product(
            title='محمد خارج از بازه',
            product_code='ART-COMBO-DATE-SORT-3',
            status=ProductStatusChoices.DRAFT,
            source_type=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
            suggestion_date=date(2026, 5, 1),
        )
        self.create_product(
            title='محمد با نوع هنر دیگر',
            product_code='ART-COMBO-DATE-SORT-4',
            status=ProductStatusChoices.DRAFT,
            source_type=ProductSourceTypeChoices.MANUAL,
            art_type='sculpture',
            suggestion_date=date(2026, 3, 15),
        )

        response = self.get_list(
            user=self.authorized_user,
            q='محمد',
            status=ProductStatusChoices.DRAFT,
            source=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
            date_from='2026-03-01',
            date_to='2026-03-31',
            sort='title',
        )

        self.assertEqual(
            list(response.context['products']),
            [first_matching_product, second_matching_product],
        )

    def test_pagination_preserves_all_active_query_parameters(self):
        for index in range(21):
            self.create_product(
                title=f'محمد مشترک {index}',
                product_code=f'ART-PAGINATION-FILTER-{index}',
                status=ProductStatusChoices.DRAFT,
                source_type=ProductSourceTypeChoices.MANUAL,
                art_type='painting',
                suggestion_date=date(2026, 4, 1),
            )

        response = self.get_list(
            user=self.authorized_user,
            q='محمد',
            status=ProductStatusChoices.DRAFT,
            source=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
            date_from='2026-01-01',
            date_to='2026-08-22',
            sort='-created_at',
        )

        self.assertContains(
            response,
            '?q=%D9%85%D8%AD%D9%85%D8%AF&amp;status=DRAFT&amp;source=MANUAL&amp;art_type=painting&amp;date_from=2026-01-01&amp;date_to=2026-08-22&amp;sort=-created_at&amp;page=2',
            html=False,
        )

    def test_clear_filters_preserves_search_query(self):
        self.create_product(
            title='محمد و هنر',
            product_code='ART-CLEAR-FILTER-1',
            status=ProductStatusChoices.DRAFT,
            source_type=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
        )

        response = self.get_list(
            user=self.authorized_user,
            q='محمد',
            status=ProductStatusChoices.DRAFT,
            source=ProductSourceTypeChoices.MANUAL,
            art_type='painting',
            date_from='2026-01-01',
            date_to='2026-08-22',
            sort='title',
        )

        self.assertContains(response, 'href="/products/?q=%D9%85%D8%AD%D9%85%D8%AF">حذف فیلترها</a>', html=False)


class ProductDetailViewTests(ProductCreateBaseTestCase):
    def get_detail(self, product, *, user=None, next_url=None):
        if user is not None:
            self.client.force_login(user)

        url = reverse('products:detail', args=[product.pk])
        if next_url:
            url = f'{url}?{urlencode({"next": next_url})}'
        return self.client.get(url)

    def create_detail_product(self, **overrides):
        payload = {
            'title': 'تابلوی قاجاری',
            'product_code': 'ART-DETAIL-1',
            'description': 'توضیح کامل اثر برای نمایش در صفحه جزئیات',
            'artist': 'هنرمند نامدار',
            'production_date': date(2024, 5, 20),
            'production_location': 'تهران',
            'material': 'رنگ روغن روی بوم',
            'subject': 'منظره',
            'usage': 'تزئینی',
            'art_type': 'نقاشی',
            'suggested_by': 'سارا احمدی',
            'contact_method': ContactMethodChoices.WHATSAPP,
            'suggestion_date': date(2026, 8, 20),
            'suggested_price': '3500000',
            'suitable_price': '3200000',
            'status': ProductStatusChoices.PENDING_REVIEW,
            'source_type': ProductSourceTypeChoices.MANUAL,
            'source_name': 'ثبت داخلی',
            'source_url': 'https://example.com/products/detail-1',
            'is_cancelled': True,
            'is_notable': True,
            'needs_expert_review': True,
            'created_by': self.operator_user,
            'updated_by': self.admin_user,
        }
        payload.update(overrides)
        return Product.objects.create(**payload)

    def test_anonymous_cannot_access(self):
        product = self.create_detail_product()

        response = self.get_detail(product)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('products:detail', args=[product.pk])}",
        )

    def test_viewer_can_access(self):
        product = self.create_detail_product()

        response = self.get_detail(product, user=self.viewer_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.title)

    def test_operator_can_access(self):
        product = self.create_detail_product()

        response = self.get_detail(product, user=self.operator_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.title)

    def test_admin_can_access(self):
        product = self.create_detail_product()

        response = self.get_detail(product, user=self.admin_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.title)

    def test_product_detail_works(self):
        product = self.create_detail_product()

        response = self.get_detail(product, user=self.viewer_user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'].pk, product.pk)

    def test_invalid_product_id_returns_404(self):
        self.client.force_login(self.viewer_user)

        response = self.client.get(reverse('products:detail', args=[999999]))

        self.assertEqual(response.status_code, 404)

    def test_product_information_displayed(self):
        product = self.create_detail_product()

        response = self.get_detail(product, user=self.viewer_user)

        self.assertContains(response, 'تابلوی قاجاری')
        self.assertContains(response, 'ART-DETAIL-1')
        self.assertContains(response, 'توضیح کامل اثر برای نمایش در صفحه جزئیات')
        self.assertContains(response, 'هنرمند نامدار')
        self.assertContains(response, 'تهران')
        self.assertContains(response, 'رنگ روغن روی بوم')
        self.assertContains(response, 'منظره')
        self.assertContains(response, 'تزئینی')
        self.assertContains(response, 'نقاشی')
        self.assertContains(response, 'سارا احمدی')
        self.assertContains(response, 'واتساپ')
        self.assertContains(response, '3500000')
        self.assertContains(response, '3200000')
        self.assertContains(response, str(self.operator_user))
        self.assertContains(response, str(self.admin_user))

    def test_primary_image_displayed(self):
        product = self.create_detail_product()
        primary_image = ProductImage.objects.create(
            product=product,
            image=self.create_test_image('primary-detail.jpg'),
            is_primary=True,
            sort_order=5,
        )
        ProductImage.objects.create(
            product=product,
            image=self.create_test_image('secondary-detail.jpg'),
            is_primary=False,
            sort_order=1,
        )

        response = self.get_detail(product, user=self.viewer_user)

        self.assertEqual(response.context['primary_image'].pk, primary_image.pk)
        self.assertContains(response, 'id="product-main-image"', html=False)
        self.assertContains(response, primary_image.image.url)

    def test_multiple_images_displayed(self):
        product = self.create_detail_product()
        first_image = ProductImage.objects.create(
            product=product,
            image=self.create_test_image('detail-one.jpg'),
            is_primary=True,
            sort_order=0,
        )
        second_image = ProductImage.objects.create(
            product=product,
            image=self.create_test_image('detail-two.jpg'),
            is_primary=False,
            sort_order=1,
        )

        response = self.get_detail(product, user=self.viewer_user)

        self.assertContains(response, first_image.image.url)
        self.assertContains(response, second_image.image.url)
        self.assertEqual(len(response.context['gallery_images']), 2)

    def test_images_ordered_by_sort_order(self):
        product = self.create_detail_product()
        primary_image = ProductImage.objects.create(
            product=product,
            image=self.create_test_image('detail-primary.jpg'),
            is_primary=True,
            sort_order=10,
        )
        first_secondary = ProductImage.objects.create(
            product=product,
            image=self.create_test_image('detail-secondary-1.jpg'),
            is_primary=False,
            sort_order=1,
        )
        second_secondary = ProductImage.objects.create(
            product=product,
            image=self.create_test_image('detail-secondary-2.jpg'),
            is_primary=False,
            sort_order=2,
        )

        response = self.get_detail(product, user=self.viewer_user)

        self.assertEqual(
            [image.pk for image in response.context['gallery_images']],
            [primary_image.pk, first_secondary.pk, second_secondary.pk],
        )

    def test_product_without_image_works(self):
        product = self.create_detail_product()

        response = self.get_detail(product, user=self.viewer_user)

        self.assertIsNone(response.context['primary_image'])
        self.assertContains(response, 'بدون تصویر')

    def test_status_displayed(self):
        product = self.create_detail_product(status=ProductStatusChoices.REJECTED)

        response = self.get_detail(product, user=self.viewer_user)

        self.assertContains(response, 'رد شده')
        self.assertContains(response, 'status-badge-rejected')

    def test_flags_displayed(self):
        product = self.create_detail_product(
            is_cancelled=True,
            is_notable=True,
            needs_expert_review=True,
        )

        response = self.get_detail(product, user=self.viewer_user)

        self.assertContains(response, 'انصراف داده شده')
        self.assertContains(response, 'قابل توجه')
        self.assertContains(response, 'نیازمند کارشناسی')

    def test_source_displayed(self):
        product = self.create_detail_product(
            source_type=ProductSourceTypeChoices.OTHER_AUCTION,
            source_name='حراج تهران',
            source_url='https://example.com/auction/product-1',
        )

        response = self.get_detail(product, user=self.viewer_user)

        self.assertContains(response, 'سایر مزایده‌ها')
        self.assertContains(response, 'حراج تهران')
        self.assertContains(response, 'https://example.com/auction/product-1')

    def test_back_button_preserves_products_query_when_next_is_provided(self):
        product = self.create_detail_product()

        response = self.get_detail(
            product,
            user=self.viewer_user,
            next_url='/products/?q=%D9%85%D8%AD%D9%85%D8%AF&status=DRAFT',
        )

        self.assertContains(
            response,
            'href="/products/?q=%D9%85%D8%AD%D9%85%D8%AF&amp;status=DRAFT"',
            count=2,
            html=False,
        )


class ProductEditViewTests(ProductCreateBaseTestCase):
    def get_edit(self, product_id, *, user=None):
        if user is not None:
            self.client.force_login(user)

        return self.client.get(reverse('products:edit', args=[product_id]))

    def post_edit(self, product_id, *, user=None, data=None, follow=False):
        self.client.force_login(user or self.operator_user)
        return self.client.post(
            reverse('products:edit', args=[product_id]),
            data=data or self.get_edit_payload(),
            follow=follow,
        )

    def create_edit_product(self, **overrides):
        payload = {
            'title': 'اثر قابل ویرایش',
            'product_code': 'ART-EDIT-1',
            'description': 'توضیحات اولیه محصول',
            'artist': 'هنرمند اولیه',
            'production_date': date(2024, 2, 10),
            'production_location': 'اصفهان',
            'material': 'اکرلیک',
            'subject': 'پرتره',
            'usage': 'نمایشی',
            'art_type': 'نقاشی',
            'suggested_by': 'مهدی وکیلی',
            'contact_method': ContactMethodChoices.TELEGRAM,
            'suggestion_date': date(2026, 8, 20),
            'suggested_price': '1200000',
            'suitable_price': '1000000',
            'status': ProductStatusChoices.PENDING_REVIEW,
            'source_type': ProductSourceTypeChoices.MANUAL,
            'source_name': 'منبع داخلی',
            'source_url': 'https://example.com/source/edit-product',
            'is_cancelled': False,
            'is_notable': True,
            'needs_expert_review': False,
            'created_by': self.admin_user,
            'updated_by': self.admin_user,
        }
        payload.update(overrides)
        return Product.objects.create(**payload)

    def get_edit_payload(self, **overrides):
        payload = {
            'suggested_by': 'سمیه فرهادی',
            'contact_method': ContactMethodChoices.WHATSAPP,
            'suggestion_date': '2026-08-21',
            'title': 'اثر ویرایش‌شده',
            'product_code': 'ART-EDIT-UPDATED-1',
            'description': 'توضیحات به‌روزشده',
            'artist': 'هنرمند جدید',
            'production_date': '2024-06-01',
            'production_location': 'شیراز',
            'material': 'رنگ روغن',
            'subject': 'طبیعت',
            'usage': 'دکوراتیو',
            'art_type': 'تابلو',
            'suggested_price': '2500000',
            'suitable_price': '2300000',
            'is_cancelled': 'on',
            'is_notable': '',
            'needs_expert_review': 'on',
        }
        payload.update(overrides)
        return payload

    def test_anonymous_cannot_edit(self):
        product = self.create_edit_product()

        response = self.get_edit(product.pk)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('products:edit', args=[product.pk])}",
        )

    def test_viewer_cannot_edit(self):
        product = self.create_edit_product()

        response = self.get_edit(product.pk, user=self.viewer_user)

        self.assertEqual(response.status_code, 403)

    def test_operator_can_edit(self):
        product = self.create_edit_product()

        response = self.get_edit(product.pk, user=self.operator_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ویرایش محصول')

    def test_admin_can_edit(self):
        product = self.create_edit_product()

        response = self.get_edit(product.pk, user=self.admin_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ویرایش محصول')

    def test_edit_page_loads(self):
        product = self.create_edit_product()

        response = self.get_edit(product.pk, user=self.operator_user)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_edit.html')
        self.assertContains(response, 'ذخیره تغییرات')
        self.assertContains(response, 'انصراف')

    def test_existing_values_displayed(self):
        product = self.create_edit_product()

        response = self.get_edit(product.pk, user=self.operator_user)

        self.assertContains(response, 'value="اثر قابل ویرایش"', html=False)
        self.assertContains(response, 'value="ART-EDIT-1"', html=False)
        self.assertContains(response, 'توضیحات اولیه محصول')
        self.assertContains(response, 'value="مهدی وکیلی"', html=False)

    def test_valid_update_works(self):
        product = self.create_edit_product()

        response = self.post_edit(product.pk, data=self.get_edit_payload(), follow=True)

        product.refresh_from_db()
        self.assertRedirects(response, reverse('products:detail', args=[product.pk]))
        self.assertEqual(product.title, 'اثر ویرایش‌شده')
        self.assertEqual(product.product_code, 'ART-EDIT-UPDATED-1')
        self.assertEqual(product.description, 'توضیحات به‌روزشده')
        self.assertEqual(product.artist, 'هنرمند جدید')
        self.assertTrue(product.is_cancelled)
        self.assertFalse(product.is_notable)
        self.assertTrue(product.needs_expert_review)

    def test_updated_by_updated_correctly(self):
        product = self.create_edit_product(updated_by=self.admin_user)

        self.post_edit(product.pk, user=self.operator_user, data=self.get_edit_payload())

        product.refresh_from_db()
        self.assertEqual(product.updated_by, self.operator_user)

    def test_created_by_remains_unchanged(self):
        product = self.create_edit_product(created_by=self.admin_user)

        self.post_edit(product.pk, user=self.operator_user, data=self.get_edit_payload())

        product.refresh_from_db()
        self.assertEqual(product.created_by, self.admin_user)

    def test_status_cannot_be_changed_through_form(self):
        product = self.create_edit_product(status=ProductStatusChoices.PENDING_REVIEW)

        self.post_edit(
            product.pk,
            data=self.get_edit_payload(status=ProductStatusChoices.PUBLISHED),
        )

        product.refresh_from_db()
        self.assertEqual(product.status, ProductStatusChoices.PENDING_REVIEW)

    def test_source_type_cannot_be_changed_through_form(self):
        product = self.create_edit_product(source_type=ProductSourceTypeChoices.MANUAL)

        self.post_edit(
            product.pk,
            data=self.get_edit_payload(source_type=ProductSourceTypeChoices.CHRISTIES),
        )

        product.refresh_from_db()
        self.assertEqual(product.source_type, ProductSourceTypeChoices.MANUAL)

    def test_invalid_price_rejected(self):
        product = self.create_edit_product()

        response = self.post_edit(
            product.pk,
            data=self.get_edit_payload(suggested_price='-10'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'قیمت نمی‌تواند منفی باشد.')
        product.refresh_from_db()
        self.assertEqual(str(product.suggested_price), '1200000.00')

    def test_invalid_product_code_rejected(self):
        self.create_edit_product(product_code='ART-DUPLICATE')
        product = self.create_edit_product(product_code='ART-EDIT-UNIQUE')

        response = self.post_edit(
            product.pk,
            data=self.get_edit_payload(product_code='  ART-DUPLICATE  '),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'این کد اثر قبلاً برای پیشنهاد دستی ثبت شده است.')
        product.refresh_from_db()
        self.assertEqual(product.product_code, 'ART-EDIT-UNIQUE')

    def test_invalid_product_id_returns_404(self):
        response = self.get_edit(999999, user=self.operator_user)

        self.assertEqual(response.status_code, 404)

    def test_successful_edit_redirects_to_detail(self):
        product = self.create_edit_product()

        response = self.post_edit(product.pk, data=self.get_edit_payload())

        self.assertRedirects(response, reverse('products:detail', args=[product.pk]), fetch_redirect_response=False)

    def test_success_message_displayed(self):
        product = self.create_edit_product()

        response = self.post_edit(product.pk, data=self.get_edit_payload(), follow=True)

        self.assertRedirects(response, reverse('products:detail', args=[product.pk]))
        self.assertContains(response, 'محصول با موفقیت ویرایش شد.')
