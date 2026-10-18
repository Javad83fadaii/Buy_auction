from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from PIL import Image, ImageOps

from products.models import ProductImage


def build_thumb(rel_image: str, size: int, quality: int):
    media = Path(settings.MEDIA_ROOT)
    rel_thumb = str(PurePosixPath('thumbs') / PurePosixPath(rel_image).with_suffix('.webp'))
    dst = media / rel_thumb
    try:
        if not dst.exists():
            with Image.open(media / rel_image) as im:
                im.draft('RGB', (size, size))  # برای JPEG سریع‌تر دیکد می‌کند
                im = ImageOps.exif_transpose(im)
                im.thumbnail((size, size))
                if im.mode not in ('RGB', 'RGBA'):
                    im = im.convert('RGB')
                dst.parent.mkdir(parents=True, exist_ok=True)
                im.save(dst, 'WEBP', quality=quality)
        return rel_thumb
    except Exception:
        return None


class Command(BaseCommand):
    help = 'Generate webp thumbnails for product images (resumable).'

    def add_arguments(self, parser):
        parser.add_argument('--size', type=int, default=400)
        parser.add_argument('--quality', type=int, default=80)
        parser.add_argument('--workers', type=int, default=4)
        parser.add_argument('--batch-size', type=int, default=500)
        parser.add_argument('--primary-only', action='store_true', help='فقط عکس اصلی هر محصول')

    def handle(self, *args, **opts):
        queryset = ProductImage.objects.filter(Q(thumbnail='') | Q(thumbnail__isnull=True))
        if opts['primary_only']:
            queryset = queryset.filter(is_primary=True)
        rows = list(queryset.values_list('pk', 'image'))
        total, batch_size = len(rows), opts['batch_size']
        done = failed = 0

        with ThreadPoolExecutor(max_workers=opts['workers']) as pool:
            for start in range(0, total, batch_size):
                chunk = rows[start:start + batch_size]
                results = list(
                    pool.map(lambda r: build_thumb(r[1], opts['size'], opts['quality']), chunk)
                )
                objs = [
                    ProductImage(pk=pk, thumbnail=thumb)
                    for (pk, _), thumb in zip(chunk, results)
                    if thumb
                ]
                failed += len(chunk) - len(objs)
                if objs:
                    ProductImage.objects.bulk_update(objs, ['thumbnail'])
                done += len(objs)
                self.stdout.write(f'  {done}/{total}')

        self.stdout.write(self.style.SUCCESS(f'Thumbnails: {done} | failed: {failed}'))
        
