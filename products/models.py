import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .choices import (
    AuctionHouseChoices,
    AuctionStatusChoices,
    ContactMethodChoices,
    CurrencyChoices,
    ProductSourceTypeChoices,
    ProductStatusChoices,
)
from .validators import validate_product_image


def product_image_upload_to(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower() or '.bin'
    product_id = instance.product_id or 'unassigned'
    image_name = instance.pk or uuid.uuid4().hex
    return f'products/{product_id}/{image_name}{extension}'


class Auction(models.Model):
    name = models.CharField('نام حراجی', max_length=255, db_index=True)
    source_house = models.CharField(
        'خانه حراجی',
        max_length=32,
        choices=AuctionHouseChoices.choices,
        default=AuctionHouseChoices.OTHER,
        db_index=True,
    )
    start_date = models.DateField('تاریخ شروع', db_index=True)
    end_date = models.DateField('تاریخ پایان', blank=True, null=True)
    location = models.CharField('مکان برگزاری', max_length=255, blank=True)
    currency = models.CharField(
        'واحد پول',
        max_length=16,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.USD,
    )
    commission_rate = models.DecimalField(
        'درصد کمیسیون',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='درصد کمیسیون یا Buyer Premium حراجی (مثلاً 25 برای 25%)',
    )
    status = models.CharField(
        'وضعیت برگزاری',
        max_length=32,
        choices=AuctionStatusChoices.choices,
        default=AuctionStatusChoices.UPCOMING,
        db_index=True,
    )
    total_lots = models.PositiveIntegerField(
        'تعداد کل آثار',
        default=0,
        validators=[MinValueValidator(0)],
        help_text='تعداد کل آثار ثبت‌شده در کاتالوگ حراجی',
    )
    # آمارهای تجمیعی (امکان ورود دستی یا همگام‌سازی خودکار)
    entered_lots_count = models.PositiveIntegerField(
        'تعداد آثار وارد شده',
        default=0,
        validators=[MinValueValidator(0)],
    )
    cancelled_lots_count = models.PositiveIntegerField(
        'تعداد انصرافی',
        default=0,
        validators=[MinValueValidator(0)],
    )
    expert_lots_count = models.PositiveIntegerField(
        'تعداد کارشناسی',
        default=0,
        validators=[MinValueValidator(0)],
    )
    notable_lots_count = models.PositiveIntegerField(
        'تعداد قابل توجه',
        default=0,
        validators=[MinValueValidator(0)],
    )
    to_buy_count = models.PositiveIntegerField(
        'تعداد مواردی که باید خریداری شود',
        default=0,
        validators=[MinValueValidator(0)],
    )
    initial_info_count = models.PositiveIntegerField(
        'مواردی که اطلاعات اولیه آن وارد شده است',
        default=0,
        validators=[MinValueValidator(0)],
    )
    all_prices_count = models.PositiveIntegerField(
        'مواردی که تمام قیمت‌های آن وارد شده است',
        default=0,
        validators=[MinValueValidator(0)],
    )
    final_inspection_count = models.PositiveIntegerField(
        'مواردی که بازدید نهایی شده‌اند',
        default=0,
        validators=[MinValueValidator(0)],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_auctions',
        blank=True,
        null=True,
        verbose_name='ایجاد شده توسط',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='updated_auctions',
        blank=True,
        null=True,
        verbose_name='آخرین ویرایش توسط',
    )
    created_at = models.DateTimeField('زمان ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('زمان ویرایش', auto_now=True)

    class Meta:
        verbose_name = 'حراجی'
        verbose_name_plural = 'حراجی‌ها'
        ordering = ('-start_date', '-created_at')
        indexes = [
            models.Index(fields=['status', 'start_date'], name='auction_status_date_idx'),
            models.Index(fields=['source_house', 'status'], name='auction_house_status_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.name} ({self.get_source_house_display()})'

    def sync_statistics(self, commit: bool = True) -> dict[str, int]:
        related_products = self.products.all()
        stats = {
            'entered_lots_count': related_products.count(),
            'cancelled_lots_count': related_products.filter(is_cancelled=True).count(),
            'expert_lots_count': related_products.filter(needs_expert_review=True).count(),
            'notable_lots_count': related_products.filter(is_notable=True).count(),
            'to_buy_count': related_products.filter(to_buy=True).count(),
            'initial_info_count': related_products.filter(has_initial_info=True).count(),
            'all_prices_count': related_products.filter(has_all_prices=True).count(),
            'final_inspection_count': related_products.filter(final_inspection_done=True).count(),
        }
        for key, value in stats.items():
            setattr(self, key, value)
        if commit:
            self.save(update_fields=list(stats.keys()) + ['updated_at'])
        return stats


class Product(models.Model):
    title = models.CharField('عنوان اثر', max_length=255, db_index=True)
    product_code = models.CharField(
        'کد اثر',
        max_length=64,
        blank=True,
        null=True,
        db_index=True,
        help_text='برای جلوگیری از تداخل بین منابع مختلف، یکتایی کد در سطح source_type کنترل می‌شود.',
    )
    description = models.TextField('توضیحات', blank=True)
    suggested_price = models.DecimalField(
        'قیمت پیشنهادی',
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    suitable_price = models.DecimalField(
        'قیمت مناسب',
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    suggestion_date = models.DateField('تاریخ پیشنهاد', default=timezone.localdate, db_index=True)
    production_date = models.DateField('تاریخ تولید', blank=True, null=True)
    production_location = models.CharField('محل تولید', max_length=255, blank=True)
    artist = models.CharField('هنرمند', max_length=255, blank=True, db_index=True)
    material = models.CharField('متریال', max_length=255, blank=True)
    subject = models.CharField('موضوع', max_length=255, blank=True)
    usage = models.CharField('کاربرد', max_length=255, blank=True)
    art_type = models.CharField('نوع هنر', max_length=255, blank=True)
    suggested_by = models.CharField('پیشنهاددهنده', max_length=255, blank=True)
    contact_method = models.CharField(
        'روش پیشنهاد',
        max_length=32,
        choices=ContactMethodChoices.choices,
        blank=True,
    )
    is_cancelled = models.BooleanField('انصراف', default=False)
    is_notable = models.BooleanField('قابل توجه', default=False)
    needs_expert_review = models.BooleanField('نیازمند کارشناسی', default=False)
    assigned_expert = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_products_for_expertise',
        blank=True,
        null=True,
        verbose_name='کارشناس ارجاعی',
    )
    auction = models.ForeignKey(
        Auction,
        on_delete=models.SET_NULL,
        related_name='products',
        blank=True,
        null=True,
        verbose_name='حراجی مرتبط',
    )
    to_buy = models.BooleanField('خریداری شود', default=False, db_index=True)
    has_initial_info = models.BooleanField('اطلاعات اولیه وارد شده', default=False)
    has_all_prices = models.BooleanField('تمام قیمت‌ها وارد شده', default=False)
    final_inspection_done = models.BooleanField('بازدید نهایی شده', default=False, db_index=True)
    source_type = models.CharField(
        'نوع منبع',
        max_length=32,
        choices=ProductSourceTypeChoices.choices,
        default=ProductSourceTypeChoices.MANUAL,
    )
    source_name = models.CharField('نام منبع', max_length=255, blank=True)
    source_url = models.URLField('آدرس منبع', max_length=1000, blank=True)
    status = models.CharField(
        'وضعیت',
        max_length=32,
        choices=ProductStatusChoices.choices,
        default=ProductStatusChoices.DRAFT,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_products',
        blank=True,
        null=True,
        verbose_name='ایجاد شده توسط',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='updated_products',
        blank=True,
        null=True,
        verbose_name='آخرین ویرایش توسط',
    )
    created_at = models.DateTimeField('زمان ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('زمان ویرایش', auto_now=True)

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ('-created_at',)
        permissions = (
            ('review_product', 'Can review product'),
        )
        indexes = [
            models.Index(fields=['source_type', 'status'], name='products_src_status_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(suggested_price__gte=0) | models.Q(suggested_price__isnull=True),
                name='products_product_suggested_price_gte_0',
            ),
            models.CheckConstraint(
                condition=models.Q(suitable_price__gte=0) | models.Q(suitable_price__isnull=True),
                name='products_product_suitable_price_gte_0',
            ),
            models.UniqueConstraint(
                fields=['source_type', 'product_code'],
                name='products_product_source_type_product_code_key',
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        self._normalize_blank_fields()

    def save(self, *args, **kwargs):
        self._normalize_blank_fields()
        if self.artist:
            try:
                from expertise.models import get_or_create_artist_or_scribe
                get_or_create_artist_or_scribe(self.artist)
            except Exception:
                pass
        res = super().save(*args, **kwargs)
        if self.auction_id:
            try:
                self.auction.sync_statistics()
            except Exception:
                pass
        return res

    def delete(self, *args, **kwargs):
        auction = self.auction
        res = super().delete(*args, **kwargs)
        if auction:
            try:
                auction.sync_statistics()
            except Exception:
                pass
        return res

    def _normalize_blank_fields(self) -> None:
        if self.product_code is not None:
            self.product_code = self.product_code.strip() or None
        if self.artist:
            self.artist = ' '.join(self.artist.split())


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='محصول',
    )
    image = models.ImageField(
        'تصویر',
        upload_to=product_image_upload_to,
        validators=[validate_product_image],
    )
    is_primary = models.BooleanField('تصویر اصلی', default=False)
    sort_order = models.PositiveIntegerField(
        'ترتیب نمایش',
        default=0,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField('زمان ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'تصویر محصول'
        verbose_name_plural = 'تصاویر محصولات'
        ordering = ('sort_order', 'id')
        constraints = [
            models.CheckConstraint(
                condition=models.Q(sort_order__gte=0),
                name='products_productimage_sort_order_gte_0',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.product} - {self.sort_order}'

    def clean(self) -> None:
        super().clean()
        if not self.is_primary or not self.product_id:
            return

        existing_primary_images = type(self).objects.filter(product_id=self.product_id, is_primary=True)
        if self.pk:
            existing_primary_images = existing_primary_images.exclude(pk=self.pk)

        if existing_primary_images.exists():
            raise ValidationError({'is_primary': 'برای هر محصول فقط یک تصویر اصلی مجاز است.'})
