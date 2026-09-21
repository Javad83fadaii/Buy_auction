from django import forms
from django.contrib import admin

from .choices import ProductStatusChoices
from .models import Auction, Product, ProductImage


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'artist': forms.TextInput(
                attrs={'placeholder': 'خالق اثر / هنرمند', 'style': 'width: 100%; max-width: 25rem;'}
            ),
        }


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = (
        'title',
        'product_code',
        'to_buy',
        'has_initial_info',
        'has_all_prices',
        'final_inspection_done',
        'status',
    )
    show_change_link = True


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'source_house',
        'start_date',
        'location',
        'currency',
        'commission_rate',
        'status',
        'total_lots',
        'entered_lots_count',
        'to_buy_count',
        'final_inspection_count',
        'created_at',
    )
    list_filter = (
        'status',
        'source_house',
        'currency',
        'start_date',
        'created_at',
    )
    search_fields = ('name', 'location')
    ordering = ('-start_date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('created_by', 'updated_by')
    inlines = (ProductInline,)
    actions = ('sync_statistics_action',)

    @admin.action(description='به‌روزرسانی خودکار آمار حراجی بر اساس آثار')
    def sync_statistics_action(self, request, queryset):
        for auction in queryset:
            auction.sync_statistics()
        self.message_user(request, 'آمار حراجی‌های انتخاب‌شده با موفقیت به‌روزرسانی شد.')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ('image', 'is_primary', 'sort_order', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        'title',
        'product_code',
        'auction',
        'source_type',
        'status',
        'to_buy',
        'final_inspection_done',
        'suggested_by',
        'suggestion_date',
        'created_by',
        'is_notable',
        'needs_expert_review',
        'is_cancelled',
        'created_at',
    )
    list_filter = (
        'source_type',
        'status',
        'to_buy',
        'final_inspection_done',
        'has_initial_info',
        'has_all_prices',
        'auction',
        'contact_method',
        'is_notable',
        'needs_expert_review',
        'is_cancelled',
        'suggestion_date',
        'created_at',
    )
    search_fields = ('title', 'product_code', 'artist', 'suggested_by', 'source_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('created_by', 'updated_by', 'auction')
    inlines = (ProductImageInline,)
    actions = (
        'approve_products_action',
        'reject_products_action',
        'publish_products_action',
        'submit_review_products_action',
    )

    @admin.action(description='تأیید محصولات انتخاب‌شده')
    def approve_products_action(self, request, queryset):
        count = queryset.update(status=ProductStatusChoices.APPROVED)
        self.message_user(request, f'{count} اثر با موفقیت تأیید شد.')

    @admin.action(description='رد محصولات انتخاب‌شده')
    def reject_products_action(self, request, queryset):
        count = queryset.update(status=ProductStatusChoices.REJECTED)
        self.message_user(request, f'{count} اثر رد شد.')

    @admin.action(description='انتشار محصولات انتخاب‌شده')
    def publish_products_action(self, request, queryset):
        count = queryset.update(status=ProductStatusChoices.PUBLISHED)
        self.message_user(request, f'{count} اثر منتشر شد.')

    @admin.action(description='ارسال محصولات انتخاب‌شده برای بررسی')
    def submit_review_products_action(self, request, queryset):
        count = queryset.update(status=ProductStatusChoices.PENDING_REVIEW)
        self.message_user(request, f'{count} اثر برای بررسی ارسال شد.')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'sort_order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__title', 'product__product_code')
    ordering = ('product', 'sort_order', 'id')
    readonly_fields = ('created_at',)
    raw_id_fields = ('product',)
