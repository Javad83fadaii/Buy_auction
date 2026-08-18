from pathlib import Path

from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_PRODUCT_IMAGE_SIZE = 5 * 1024 * 1024


def validate_product_image(file) -> None:
    extension = Path(file.name).suffix.lower().lstrip('.')
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError('فرمت تصویر مجاز نیست.')

    if file.size > MAX_PRODUCT_IMAGE_SIZE:
        raise ValidationError('حجم تصویر نباید بیشتر از 5 مگابایت باشد.')

    current_position = file.tell()

    try:
        file.seek(0)
        image = Image.open(file)
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError('فایل بارگذاری‌شده یک تصویر معتبر نیست.') from exc
    finally:
        file.seek(current_position)
