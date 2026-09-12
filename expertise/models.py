from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from products.models import Product

from .choices import (
    ArtworkTypeChoices,
    AttributionCertaintyChoices,
    CalendarTypeChoices,
    ContentSubjectChoices,
    CoverTypeChoices,
    DamageTypeChoices,
    DesignPatternChoices,
    FabricTypeChoices,
    FinalVerdictChoices,
    HealthStatusChoices,
    HistoricalMatchChoices,
    IlluminationTechniqueChoices,
    InkTypeChoices,
    KnotTypeChoices,
    LanguageChoices,
    LoanTypeChoices,
    MaterialChoices,
    PaintingTypeChoices,
    ScriptChoices,
    WarpWeftMaterialChoices,
)


class ExpertAppraisal(models.Model):
    # --- هویت و شناسایی ---
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='expert_appraisal',
        verbose_name='اثر',
    )
    expert = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='expert_appraisals',
        verbose_name='کارشناس',
    )
    archive_number = models.CharField('شماره بایگانی', max_length=64, blank=True)
    loan_type = models.CharField(
        'امانی/داخلی',
        max_length=16,
        choices=LoanTypeChoices.choices,
        blank=True,
    )
    appraisal_date = models.DateField('تاریخ کارشناسی')

    # --- نوع و موضوع اثر ---
    artwork_type = models.CharField(
        'نوع اثر',
        max_length=32,
        choices=ArtworkTypeChoices.choices,
        blank=True,
    )
    content_subject = models.CharField(
        'موضوع اثر',
        max_length=32,
        choices=ContentSubjectChoices.choices,
        blank=True,
    )

    # --- تاریخ اثر ---
    inscribed_date_text = models.CharField('تاریخ ذکر شده در اثر', max_length=128, blank=True)
    calendar_type = models.CharField(
        'نوع تقویم',
        max_length=16,
        choices=CalendarTypeChoices.choices,
        blank=True,
    )
    historical_period = models.CharField('قرن/دوره تاریخی', max_length=128, blank=True)

    # --- هنرمند/کاتب ---
    artist_or_scribe_name = models.CharField('نام هنرمند/کاتب', max_length=255, blank=True)

    # --- اصالت ---
    historical_match_status = models.CharField(
        'مطابقت تاریخی با اصل اثر',
        max_length=16,
        choices=HistoricalMatchChoices.choices,
        blank=True,
    )
    attribution_certainty = models.CharField(
        'انتساب اثر به هنرمند',
        max_length=16,
        choices=AttributionCertaintyChoices.choices,
        blank=True,
    )
    signature_location = models.CharField('محل امضاء در اثر', max_length=255, blank=True)

    # --- زبان و خط ---
    language = models.CharField(
        'زبان',
        max_length=16,
        choices=LanguageChoices.choices,
        blank=True,
    )
    language_other = models.CharField('زبان (سایر)', max_length=64, blank=True)
    script = models.CharField(
        'خط',
        max_length=32,
        choices=ScriptChoices.choices,
        blank=True,
    )

    # --- مشخصات فیزیکی ---
    dimensions = models.CharField('ابعاد (سانتی‌متر)', max_length=64, blank=True)
    dimensions_with_frame = models.CharField('ابعاد با قاب (سانتی‌متر)', max_length=64, blank=True)
    dimensions_with_margin = models.CharField('ابعاد با حاشیه (سانتی‌متر)', max_length=64, blank=True)
    weight_kg = models.DecimalField(
        'وزن (کیلوگرم)',
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )

    # --- جنس ---
    material = models.CharField(
        'جنس',
        max_length=32,
        choices=MaterialChoices.choices,
        blank=True,
    )
    material_other = models.CharField('جنس (سایر)', max_length=64, blank=True)
    pages_or_pieces_count = models.PositiveIntegerField('تعداد صفحات/قطعات', blank=True, null=True)

    # --- مرکب و تکنیک ---
    ink_type = models.CharField(
        'نوع مرکب',
        max_length=16,
        choices=InkTypeChoices.choices,
        blank=True,
    )
    ink_type_other = models.CharField('نوع مرکب (سایر)', max_length=64, blank=True)
    illumination_technique = models.CharField(
        'تکنیک تذهیب/نگاره',
        max_length=16,
        choices=IlluminationTechniqueChoices.choices,
        blank=True,
    )
    illumination_technique_other = models.CharField('تکنیک تذهیب/نگاره (سایر)', max_length=64, blank=True)
    painting_type = models.CharField(
        'نوع نگاره',
        max_length=16,
        choices=PaintingTypeChoices.choices,
        blank=True,
    )
    painting_type_other = models.CharField('نوع نگاره (سایر)', max_length=64, blank=True)

    # --- جلد ---
    cover_type = models.CharField(
        'نوع جلد',
        max_length=32,
        choices=CoverTypeChoices.choices,
        blank=True,
    )

    # --- فرش و منسوجات (در صورت کاربرد) ---
    warp_material = models.CharField(
        'جنس تار',
        max_length=16,
        choices=WarpWeftMaterialChoices.choices,
        blank=True,
    )
    warp_material_other = models.CharField('جنس تار (سایر)', max_length=64, blank=True)
    weft_material = models.CharField(
        'جنس پود',
        max_length=16,
        choices=WarpWeftMaterialChoices.choices,
        blank=True,
    )
    weft_material_other = models.CharField('جنس پود (سایر)', max_length=64, blank=True)
    fabric_type = models.CharField(
        'نوع پارچه',
        max_length=16,
        choices=FabricTypeChoices.choices,
        blank=True,
    )
    fabric_type_other = models.CharField('نوع پارچه (سایر)', max_length=64, blank=True)
    knot_type = models.CharField(
        'نوع گره',
        max_length=16,
        choices=KnotTypeChoices.choices,
        blank=True,
    )
    knot_type_other = models.CharField('نوع گره (سایر)', max_length=64, blank=True)
    design_pattern = models.CharField(
        'طرح نقشه',
        max_length=16,
        choices=DesignPatternChoices.choices,
        blank=True,
    )
    design_pattern_other = models.CharField('طرح نقشه (سایر)', max_length=64, blank=True)

    # --- وضعیت سلامت ---
    health_status = models.CharField(
        'وضعیت سلامت اثر',
        max_length=16,
        choices=HealthStatusChoices.choices,
        blank=True,
    )
    health_status_other = models.CharField('وضعیت سلامت اثر (سایر)', max_length=64, blank=True)

    # --- مرمت ---
    needs_restoration = models.BooleanField('نیاز به مرمت دارد', default=False)
    needs_restoration_part = models.CharField('نیاز به مرمت - کدام قسمت', max_length=255, blank=True)
    has_previous_restoration = models.BooleanField('مرمت قبلی دارد', default=False)
    previous_restoration_part = models.CharField('مرمت قبلی - کدام قسمت', max_length=255, blank=True)
    has_missing_pages = models.BooleanField('کمبود صفحات دارد', default=False)
    missing_pages_part = models.CharField('کمبود صفحات - کدام قسمت', max_length=255, blank=True)

    review_notes = models.TextField('نکات قابل بررسی در مورد اثر', blank=True)

    class Meta:
        verbose_name = 'کارشناسی اثر'
        verbose_name_plural = 'کارشناسی‌های آثار'

    def __str__(self) -> str:
        return f'کارشناسی {self.product.title} - {self.appraisal_date}'


class DamageAssessment(models.Model):
    appraisal = models.ForeignKey(
        ExpertAppraisal,
        on_delete=models.CASCADE,
        related_name='damage_assessments',
        verbose_name='کارشناسی',
    )
    damage_type = models.CharField(
        'نوع آسیب',
        max_length=32,
        choices=DamageTypeChoices.choices,
    )
    location = models.CharField('محل آسیب', max_length=255, blank=True)
    severity = models.CharField('میزان آسیب', max_length=255, blank=True)
    description = models.TextField('توضیح', blank=True)

    class Meta:
        verbose_name = 'ارزیابی آسیب'
        verbose_name_plural = 'ارزیابی‌های آسیب'
        ordering = ('id',)

    def __str__(self) -> str:
        return f'{self.get_damage_type_display()} - {self.appraisal_id}'
