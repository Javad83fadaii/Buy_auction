from django.contrib import admin

from .models import DamageAssessment, ExpertAppraisal


class DamageAssessmentInline(admin.TabularInline):
    model = DamageAssessment
    extra = 0
    fields = ('damage_type', 'location', 'severity', 'description')


@admin.register(ExpertAppraisal)
class ExpertAppraisalAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'expert',
        'appraisal_date',
        'artwork_type',
        'final_verdict',
        'manager_approved',
        'manager_approved_by',
        'manager_approved_at',
        'created_at',
    )
    list_filter = ('artwork_type', 'final_verdict', 'manager_approved', 'loan_type', 'appraisal_date')
    search_fields = ('product__title', 'archive_number', 'artist_or_scribe_name', 'owner_name')
    ordering = ('-appraisal_date',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('product', 'expert', 'manager_approved_by', 'created_by', 'updated_by')
    inlines = (DamageAssessmentInline,)
