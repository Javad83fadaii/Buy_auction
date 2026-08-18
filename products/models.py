import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from .choices import ContactMethodChoices, ProductSourceTypeChoices, ProductStatusChoices
from .validators import validate_product_image


def product_image_upload_to(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower() or '.bin'
    product_id = instance.product_id or 'unassigned'
    image_name = instance.pk or uuid.uuid4().hex
    return f'products/{product_id}/{image_name}{extension}'


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
        return super().save(*args, **kwargs)

    def _normalize_blank_fields(self) -> None:
        if self.product_code is not None:
            self.product_code = self.product_code.strip() or None


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
