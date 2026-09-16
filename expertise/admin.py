from django.contrib import admin

from .forms import ExpertAppraisalAdminForm
from .models import ArtistOrScribe, DamageAssessment, ExpertAppraisal


@admin.register(ArtistOrScribe)
class ArtistOrScribeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)


class DamageAssessmentInline(admin.TabularInline):
    model = DamageAssessment
    extra = 0
    fields = ('damage_type', 'location', 'severity', 'description')


@admin.register(ExpertAppraisal)
class ExpertAppraisalAdmin(admin.ModelAdmin):
    form = ExpertAppraisalAdminForm
    list_display = (
        'product',
        'expert',
        'referred_by',
        'status',
        'is_locked',
        'manager_approved',
        'manager_approved_by',
        'appraisal_date',
        'created_at',
    )
    list_filter = (
        'status',
        'is_locked',
        'manager_approved',
        'artwork_type',
        'final_verdict',
        'loan_type',
        'appraisal_date',
    )
    search_fields = ('product__title', 'product__product_code', 'artist_or_scribe_name', 'owner_name')
    ordering = ('-appraisal_date', '-created_at')
    readonly_fields = ('referral_date', 'created_at', 'updated_at')
    raw_id_fields = ('product', 'expert', 'referred_by', 'manager_approved_by', 'created_by', 'updated_by')
    inlines = (DamageAssessmentInline,)

    fieldsets = (
        ('هویت و ارجاع اثر', {
            'fields': (
                'product',
                'expert',
                'referred_by',
                'status',
                'is_locked',
                'loan_type',
                'loan_type_other',
                'referral_date',
                'appraisal_date',
            ),
        }),
        ('نوع و موضوع اثر', {
            'fields': (
                'artwork_type',
                'artwork_type_other',
                'content_subject',
                'content_subject_other',
            ),
        }),
        ('تاریخ اثر', {
            'fields': (
                'inscribed_date_text',
                'calendar_type',
                'calendar_type_other',
                'historical_period',
            ),
        }),
        ('هنرمند/کاتب', {
            'fields': ('artist_or_scribe_name',),
        }),
        ('اصالت و انتساب', {
            'fields': (
                'historical_match_status',
                'historical_match_status_other',
                'attribution_certainty',
                'attribution_certainty_other',
                'signature_location',
            ),
        }),
        ('زبان و خط', {
            'fields': (
                'language',
                'language_other',
                'script',
                'script_other',
            ),
        }),
        ('مشخصات فیزیکی', {
            'fields': (
                'dimensions',
                'dimensions_with_frame',
                'dimensions_with_margin',
                'weight_kg',
            ),
        }),
        ('جنس و قطعات', {
            'fields': (
                'material',
                'material_other',
                'pages_or_pieces_count',
            ),
        }),
        ('مرکب و تکنیک نگاره', {
            'fields': (
                'ink_type',
                'ink_type_other',
                'illumination_technique',
                'illumination_technique_other',
                'painting_type',
                'painting_type_other',
            ),
        }),
        ('جلد', {
            'fields': (
                'cover_type',
                'cover_type_other',
            ),
        }),
        ('فرش و منسوجات (در صورت کاربرد)', {
            'classes': ('collapse',),
            'fields': (
                'warp_material',
                'warp_material_other',
                'weft_material',
                'weft_material_other',
                'fabric_type',
                'fabric_type_other',
                'knot_type',
                'knot_type_other',
                'design_pattern',
                'design_pattern_other',
            ),
        }),
        ('وضعیت سلامت و مرمت', {
            'fields': (
                'health_status',
                'health_status_other',
                'needs_restoration',
                'needs_restoration_part',
                'has_previous_restoration',
                'previous_restoration_part',
                'has_missing_pages',
                'missing_pages_part',
            ),
        }),
        ('تحلیل پژوهشی', {
            'classes': ('collapse',),
            'fields': (
                'review_notes',
                'introduction',
                'historical_importance',
                'artistic_importance',
                'unique_features',
                'expert_opinion',
                'references',
                'marginal_notes',
            ),
        }),
        ('ارزش‌گذاری و قیمت‌گذاری', {
            'fields': (
                'seller_suggested_price_toman',
                'expert_suggested_price_toman',
                'final_auction_price_toman',
                'final_price_usd',
                'usd_exchange_rate',
                'gold_18k_gram_price_toman',
            ),
        }),
        ('مالک و دریافت اثر', {
            'fields': (
                'owner_name',
                'received_date',
            ),
        }),
        ('نتیجه نهایی کارشناسی', {
            'fields': (
                'final_result_summary',
                'final_verdict',
                'final_verdict_other',
            ),
        }),
        ('تأیید مدیر', {
            'fields': (
                'manager_approved',
                'manager_approved_at',
                'manager_approved_by',
            ),
        }),
        ('اطلاعات سیستمی', {
            'classes': ('collapse',),
            'fields': (
                'created_by',
                'updated_by',
                'created_at',
                'updated_at',
            ),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj=obj))
        if obj and obj.is_locked:
            all_fields = [f.name for f in obj._meta.fields if f.name != 'is_locked']
            for field in all_fields:
                if field not in readonly:
                    readonly.append(field)
        return readonly
