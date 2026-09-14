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
    search_fields = ('product__title', 'archive_number', 'artist_or_scribe_name', 'owner_name')
    ordering = ('-appraisal_date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('product', 'expert', 'referred_by', 'manager_approved_by', 'created_by', 'updated_by')
    inlines = (DamageAssessmentInline,)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj=obj))
        if obj and obj.is_locked:
            all_fields = [f.name for f in obj._meta.fields if f.name != 'is_locked']
            for field in all_fields:
                if field not in readonly:
                    readonly.append(field)
        return readonly

