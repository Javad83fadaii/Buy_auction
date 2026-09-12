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

# مدل‌های ExpertAppraisal و DamageAssessment در فازهای بعدی اضافه می‌شوند.
