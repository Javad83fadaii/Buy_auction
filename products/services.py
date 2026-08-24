from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max

from .choices import ProductSourceTypeChoices, ProductStatusChoices
from .models import Product, ProductImage

MANUAL_PRODUCT_FORM_FIELDS = (
    'suggested_by',
    'contact_method',
    'suggestion_date',
    'title',
    'product_code',
    'description',
    'artist',
    'production_date',
    'production_location',
    'material',
    'subject',
    'usage',
    'art_type',
    'suggested_price',
    'suitable_price',
    'is_cancelled',
    'is_notable',
    'needs_expert_review',
)


def create_manual_product(*, cleaned_data: dict, images: list, user) -> Product:
    product = Product(
        **{field: cleaned_data.get(field) for field in MANUAL_PRODUCT_FORM_FIELDS},
        source_type=ProductSourceTypeChoices.MANUAL,
        status=ProductStatusChoices.DRAFT,
        created_by=user,
        updated_by=user,
    )

    try:
        product.full_clean()
        image_instances = _build_product_images(product=product, images=images)

        with transaction.atomic():
            product.save()
            for image_instance in image_instances:
                image_instance.save()
    except ValidationError as exc:
        raise _normalize_validation_error(exc, product=product) from exc
    except IntegrityError as exc:
        raise _normalize_integrity_error(exc, product=product) from exc

    return product


def _build_product_images(*, product: Product, images: list) -> list[ProductImage]:
    image_instances: list[ProductImage] = []

    for sort_order, image in enumerate(images):
        image_instance = ProductImage(
            product=product,
            image=image,
            is_primary=sort_order == 0,
            sort_order=sort_order,
        )
        image_instance.full_clean(exclude={'product'})
        image_instances.append(image_instance)

    return image_instances


def add_product_image(*, product: Product, image) -> ProductImage:
    with transaction.atomic():
        product_images = ProductImage.objects.select_for_update().filter(product=product)
        max_sort_order = product_images.aggregate(max_sort_order=Max('sort_order'))['max_sort_order']
        image_instance = ProductImage(
            product=product,
            image=image,
            is_primary=not product_images.filter(is_primary=True).exists(),
            sort_order=0 if max_sort_order is None else max_sort_order + 1,
        )
        image_instance.full_clean()
        image_instance.save()
    return image_instance


def set_product_image_primary(*, product: Product, image: ProductImage) -> ProductImage:
    with transaction.atomic():
        product_images = ProductImage.objects.select_for_update().filter(product=product)
        target_image = product_images.get(pk=image.pk)
        product_images.exclude(pk=target_image.pk).filter(is_primary=True).update(is_primary=False)

        if not target_image.is_primary:
            target_image.is_primary = True
            target_image.full_clean()
            target_image.save(update_fields=['is_primary'])

    return target_image


def update_product_image_sort_order(
    *,
    product: Product,
    image: ProductImage,
    sort_order: int,
) -> ProductImage:
    with transaction.atomic():
        managed_image = ProductImage.objects.select_for_update().get(pk=image.pk, product=product)
        managed_image.sort_order = sort_order
        managed_image.full_clean()
        managed_image.save(update_fields=['sort_order'])
    return managed_image


def delete_product_image(*, product: Product, image: ProductImage) -> None:
    with transaction.atomic():
        product_images = ProductImage.objects.select_for_update().filter(product=product).order_by(
            'sort_order',
            'id',
        )
        target_image = product_images.get(pk=image.pk)
        replacement_image = product_images.exclude(pk=target_image.pk).first()
        target_was_primary = target_image.is_primary

        target_image.delete()

        if target_was_primary and replacement_image is not None:
            ProductImage.objects.filter(product=product).update(is_primary=False)
            replacement_image.is_primary = True
            replacement_image.full_clean()
            replacement_image.save(update_fields=['is_primary'])


def _normalize_validation_error(exc: ValidationError, *, product: Product) -> ValidationError:
    error_dict = getattr(exc, 'error_dict', None)
    if not error_dict:
        return exc

    non_field_errors = error_dict.get(NON_FIELD_ERRORS, [])
    if product.product_code and any(error.code in {'unique', 'unique_together'} for error in non_field_errors):
        message_dict = {
            field_name: [error.message for error in errors]
            for field_name, errors in error_dict.items()
            if field_name != NON_FIELD_ERRORS
        }
        message_dict.setdefault('product_code', []).append(
            'این کد اثر قبلاً برای پیشنهاد دستی ثبت شده است.'
        )

        remaining_non_field_errors = [
            error.message for error in non_field_errors if error.code not in {'unique', 'unique_together'}
        ]
        if remaining_non_field_errors:
            message_dict[NON_FIELD_ERRORS] = remaining_non_field_errors

        return ValidationError(message_dict)

    return exc


def _normalize_integrity_error(exc: IntegrityError, *, product: Product) -> ValidationError:
    if product.product_code:
        return ValidationError({'product_code': 'این کد اثر قبلاً برای پیشنهاد دستی ثبت شده است.'})

    return ValidationError('ثبت اثر با خطا مواجه شد. لطفاً دوباره تلاش کنید.')
