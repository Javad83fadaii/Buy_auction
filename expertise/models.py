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

    class Meta:
        verbose_name = 'کارشناسی اثر'
        verbose_name_plural = 'کارشناسی‌های آثار'

    def __str__(self) -> str:
        return f'کارشناسی {self.product.title} - {self.appraisal_date}'
