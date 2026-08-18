from django.contrib import admin

from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ('image', 'is_primary', 'sort_order', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'product_code',
        'source_type',
        'status',
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
    raw_id_fields = ('created_by', 'updated_by')
    inlines = (ProductImageInline,)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'sort_order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__title', 'product__product_code')
    ordering = ('product', 'sort_order', 'id')
    readonly_fields = ('created_at',)
    raw_id_fields = ('product',)
