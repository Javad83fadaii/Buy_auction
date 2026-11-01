"""تصاویر آثار که به‌صورت فایل روی دیسک و در مسیر MEDIA_ROOT/lots ذخیره می‌شوند.

ساختار پوشه‌ها:
    lots/<پوشه حراجی>/<شماره اثر>/000.jpg
    lots/<پوشه حراجی>/<شماره اثر>/001.jpg ...

تصویر اصلی فایلی است که نام آن با «00» شروع می‌شود و بقیه تصاویر در گالری
(تصاویر بیشتر) نمایش داده می‌شوند. نام پوشه حراجی همیشه با شماره مزایده یکسان
نیست (مثلاً شناسه فروش در کریستیز)، بنابراین پوشه هر اثر از روی نام پوشه اثر
شناسایی می‌شود.
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from django.conf import settings

LOT_IMAGE_ROOT = 'lots'
PRIMARY_IMAGE_PREFIX = '00'
IMAGE_EXTENSIONS = frozenset({'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff'})
# پس از این مدت، پوشه‌ها دوباره اسکن می‌شوند تا تصاویر تازه‌دانلودشده بدون ری‌استارت دیده شوند.
INDEX_CACHE_TTL_SECONDS = 60


@dataclass(frozen=True)
class LotImage:
    """یک تصویر از پوشه اثر روی دیسک با امضایی مشابه ProductImage."""

    name: str
    path: str
    url: str
    is_primary: bool = False
    sort_order: int = 0

    @property
    def key(self) -> str:
        return self.path

    @property
    def display_url(self) -> str:
        return self.url

    @property
    def original_url(self) -> str:
        return self.url


def _media_root() -> Path:
    return Path(settings.MEDIA_ROOT)


def _media_url_prefix() -> str:
    media_url = settings.MEDIA_URL or '/media/'
    return media_url if media_url.endswith('/') else f'{media_url}/'


_INDEX_CACHE: dict[str, tuple[float, dict[str, str]]] = {}


def _build_lot_directory_index(media_root: str) -> dict[str, str]:
    """نگاشت «نام پوشه اثر» به «نام پوشه حراجی» در مسیر MEDIA_ROOT/lots."""
    index: dict[str, str] = {}
    try:
        auction_dirs = sorted(
            (entry for entry in os.scandir(Path(media_root) / LOT_IMAGE_ROOT) if entry.is_dir()),
            key=lambda entry: entry.name,
        )
    except OSError:
        return index

    for auction_dir in auction_dirs:
        try:
            lot_entries = os.scandir(auction_dir.path)
        except OSError:
            continue
        with lot_entries:
            for entry in lot_entries:
                if entry.is_dir():
                    index.setdefault(entry.name, auction_dir.name)
    return index


def _lot_directory_index(media_root: str) -> dict[str, str]:
    """نسخه کش‌شده نگاشت پوشه‌ها؛ پس از انقضای TTL دوباره اسکن می‌شود."""
    cached_entry = _INDEX_CACHE.get(media_root)
    now = time.monotonic()
    if cached_entry and now - cached_entry[0] < INDEX_CACHE_TTL_SECONDS:
        return cached_entry[1]
    index = _build_lot_directory_index(media_root)
    _INDEX_CACHE[media_root] = (now, index)
    return index


def reset_lot_image_index() -> None:
    """پاک‌کردن کش نگاشت پوشه‌ها (پس از دانلود تصاویر جدید)."""
    _INDEX_CACHE.clear()


def get_product_lot_number(product) -> str:
    """شماره اثر از روی کد محصول؛ کد به شکل «شماره مزایده-شماره اثر» است."""
    product_code = str(getattr(product, 'product_code', '') or '').strip()
    if not product_code:
        return ''
    if '-' in product_code:
        return product_code.rsplit('-', 1)[-1].strip()
    return product_code


def get_lot_image_directory(product) -> str:
    """مسیر نسبی پوشه تصاویر اثر (نسبت به MEDIA_ROOT) یا رشته خالی."""
    lot_number = get_product_lot_number(product)
    if not lot_number:
        return ''
    auction_directory_name = _lot_directory_index(str(_media_root())).get(lot_number)
    if not auction_directory_name:
        return ''
    return f'{LOT_IMAGE_ROOT}/{auction_directory_name}/{lot_number}'


def _list_image_file_names(directory: Path) -> list[str]:
    try:
        entries = list(os.scandir(directory))
    except OSError:
        return []
    file_names = [
        entry.name
        for entry in entries
        if entry.is_file() and Path(entry.name).suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(file_names, key=lambda name: (not name.startswith(PRIMARY_IMAGE_PREFIX), name.lower()))


def list_lot_images(product) -> list[LotImage]:
    """تصاویر اثر روی دیسک؛ تصویر اصلی (شروع‌شده با 00) همیشه اولین عضو است."""
    directory = get_lot_image_directory(product)
    if not directory:
        return []

    absolute_directory = _media_root().joinpath(*directory.split('/'))
    file_names = _list_image_file_names(absolute_directory)
    if not file_names:
        return []

    url_prefix = _media_url_prefix()
    primary_name = next(
        (name for name in file_names if name.startswith(PRIMARY_IMAGE_PREFIX)),
        file_names[0],
    )
    return [
        LotImage(
            name=name,
            path=f'{directory}/{name}',
            url=f'{url_prefix}{quote(f"{directory}/{name}")}',
            is_primary=name == primary_name,
            sort_order=index,
        )
        for index, name in enumerate(file_names)
    ]
