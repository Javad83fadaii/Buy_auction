from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import TestCase

from products.choices import ProductSourceTypeChoices, ProductStatusChoices
from products.forms import ProductCreateForm
from products.models import Product

from .admin import ArtistOrScribeAdmin, ExpertAppraisalAdmin
from .forms import ArtistOrScribeDatalistWidget, ExpertAppraisalAdminForm
from .models import (
    ArtistOrScribe,
    ExpertAppraisal,
    get_artist_or_scribe_names,
    get_or_create_artist_or_scribe,
)

User = get_user_model()


class ArtistOrScribeModelAndHelperTests(TestCase):
    def test_artist_or_scribe_str_and_clean(self):
        artist = ArtistOrScribe(name='  میرعماد حسنی  ')
        artist.clean()
        self.assertEqual(artist.name, 'میرعماد حسنی')
        artist.save()
        self.assertEqual(str(artist), 'میرعماد حسنی')

    def test_get_or_create_artist_or_scribe_creates_and_retrieves(self):
        self.assertIsNone(get_or_create_artist_or_scribe(''))
        self.assertIsNone(get_or_create_artist_or_scribe('   '))
        self.assertIsNone(get_or_create_artist_or_scribe(None))

        artist1 = get_or_create_artist_or_scribe('  رضا عباسی  ')
        self.assertIsNotNone(artist1)
        self.assertEqual(artist1.name, 'رضا عباسی')
        self.assertEqual(ArtistOrScribe.objects.count(), 1)

        # Calling again should retrieve the same instance without duplicate
        artist2 = get_or_create_artist_or_scribe('رضا عباسی')
        self.assertEqual(artist1.pk, artist2.pk)
        self.assertEqual(ArtistOrScribe.objects.count(), 1)

    def test_get_artist_or_scribe_names(self):
        ArtistOrScribe.objects.create(name='کمال‌الدین بهزاد')
        ArtistOrScribe.objects.create(name='احمد نیریزی')
        ArtistOrScribe.objects.create(name='میرعماد حسنی')

        names = get_artist_or_scribe_names()
        self.assertEqual(set(names), {'کمال‌الدین بهزاد', 'احمد نیریزی', 'میرعماد حسنی'})
        self.assertEqual(len(names), 3)


class ExpertAppraisalArtistIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='expert_user',
            password='Password123!',
            first_name='علی',
            last_name='کارشناس',
        )
        self.product = Product.objects.create(
            title='مرقع خط کهن',
            product_code='COD-001',
            source_type=ProductSourceTypeChoices.MANUAL,
            status=ProductStatusChoices.APPROVED,
        )

    def test_appraisal_save_automatically_creates_artist_or_scribe(self):
        self.assertEqual(ArtistOrScribe.objects.count(), 0)

        appraisal = ExpertAppraisal.objects.create(
            product=self.product,
            expert=self.user,
            artist_or_scribe_name='  درویش عبدالمجید طالقانی  ',
        )

        # Field should be stripped
        self.assertEqual(appraisal.artist_or_scribe_name, 'درویش عبدالمجید طالقانی')

        # ArtistOrScribe model should have the entry
        artist_obj = ArtistOrScribe.objects.filter(name='درویش عبدالمجید طالقانی').first()
        self.assertIsNotNone(artist_obj)

    def test_appraisal_save_with_existing_artist_does_not_duplicate(self):
        ArtistOrScribe.objects.create(name='یاقوت مستعصمی')
        self.assertEqual(ArtistOrScribe.objects.count(), 1)

        ExpertAppraisal.objects.create(
            product=self.product,
            expert=self.user,
            artist_or_scribe_name='یاقوت مستعصمی',
        )

        self.assertEqual(ArtistOrScribe.objects.count(), 1)


class ProductArtistIntegrationTests(TestCase):
    def test_product_save_creates_artist_in_shared_database(self):
        self.assertEqual(ArtistOrScribe.objects.count(), 0)

        product = Product.objects.create(
            title='تابلو مینیاتور صفوی',
            artist='  محمود فرشچیان  ',
            source_type=ProductSourceTypeChoices.MANUAL,
        )

        self.assertEqual(product.artist, 'محمود فرشچیان')
        self.assertTrue(ArtistOrScribe.objects.filter(name='محمود فرشچیان').exists())

        # Creating another product with same artist should not duplicate
        Product.objects.create(
            title='اثر دوم',
            artist='محمود فرشچیان',
            source_type=ProductSourceTypeChoices.MANUAL,
        )
        self.assertEqual(ArtistOrScribe.objects.filter(name='محمود فرشچیان').count(), 1)


class DatalistWidgetAndFormTests(TestCase):
    def setUp(self):
        ArtistOrScribe.objects.create(name='میرزا غلامرضا اصفهانی')
        ArtistOrScribe.objects.create(name='میرحسین خوشنویس')

    def test_datalist_widget_renders_input_and_datalist_options(self):
        widget = ArtistOrScribeDatalistWidget()
        html = widget.render('artist_or_scribe_name', 'میرحسین خوشنویس', attrs={'id': 'id_custom_artist'})

        # Must have list attribute linked to datalist id
        self.assertIn('list="id_custom_artist_list"', html)
        self.assertIn('<datalist id="id_custom_artist_list">', html)
        self.assertIn('<option value="میرزا غلامرضا اصفهانی">', html)
        self.assertIn('<option value="میرحسین خوشنویس">', html)

    def test_expert_appraisal_admin_form_has_datalist_widget(self):
        form = ExpertAppraisalAdminForm()
        self.assertIsInstance(form.fields['artist_or_scribe_name'].widget, ArtistOrScribeDatalistWidget)

    def test_product_create_form_has_datalist_widget(self):
        form = ProductCreateForm()
        self.assertIsInstance(form.fields['artist'].widget, ArtistOrScribeDatalistWidget)
        rendered = form['artist'].as_widget()
        self.assertIn('<datalist', rendered)
        self.assertIn('میرزا غلامرضا اصفهانی', rendered)


class AdminRegistrationTests(TestCase):
    def test_admin_registrations(self):
        self.assertIn(ArtistOrScribe, site._registry)
        self.assertIn(ExpertAppraisal, site._registry)
        self.assertIsInstance(site._registry[ArtistOrScribe], ArtistOrScribeAdmin)
        self.assertIsInstance(site._registry[ExpertAppraisal], ExpertAppraisalAdmin)
