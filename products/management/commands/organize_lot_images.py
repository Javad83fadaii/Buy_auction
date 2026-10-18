import shutil
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from products.choices import ProductSourceTypeChoices
from products.models import Product

ALLOWED = {'.jpg', '.jpeg', '.png', '.webp'}


def has_images(directory: Path) -> bool:
    return any(f.is_file() and f.suffix.lower() in ALLOWED for f in directory.iterdir())


def sort_key(file_path: Path):
    return (0, int(file_path.stem)) if file_path.stem.isdigit() else (1, file_path.stem.lower())


def normalize_product_directory(directory: Path, *, dry: bool) -> int:
    files = sorted(
        (file_path for file_path in directory.iterdir() if file_path.is_file() and file_path.suffix.lower() in ALLOWED),
        key=sort_key,
    )
    if not files:
        return 0

    staged_moves: list[tuple[Path, Path]] = []
    for index, file_path in enumerate(files):
        desired_name = f'{index:03d}{file_path.suffix.lower()}'
        desired_path = directory / desired_name
        if file_path.name == desired_name:
            continue
        temp_path = directory / f'__tmp__{index:03d}{file_path.suffix.lower()}'
        staged_moves.append((temp_path, desired_path))
        if not dry:
            if temp_path.exists():
                temp_path.unlink()
            file_path.rename(temp_path)

    renamed = len(staged_moves)
    if dry:
        return renamed

    for staged_path, final_path in staged_moves:
        if final_path.exists():
            final_path.unlink()
        staged_path.rename(final_path)
    return renamed


class Command(BaseCommand):
    help = 'Move media/lots/<lot_number>/ to media/lots/<auction_number>/<product_pk>/.'

    def add_arguments(self, parser):
        parser.add_argument('--folder', default='lots')
        parser.add_argument('--source', default=ProductSourceTypeChoices.CHRISTIES)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        media = Path(settings.MEDIA_ROOT)
        root = media / opts['folder']
        staging = media / f'_{opts["folder"]}_staging'
        dry = opts['dry_run']

        if not root.is_dir():
            self.stderr.write(f'Folder not found: {root}')
            return

        products = list(
            Product.objects.filter(source_type=opts['source'], auction__isnull=False)
            .select_related('auction')
        )
        code_counter = Counter(product.product_code for product in products if product.product_code)
        code_to_target = {
            product.product_code: (product.get_image_directory_name(), str(product.pk))
            for product in products
            if product.product_code and code_counter[product.product_code] == 1
        }
        ambiguous_codes = {code for code, count in code_counter.items() if count > 1}

        # مرحله ۱: پوشه‌های قدیمی (که فایل عکس مستقیم داخلشان است) به staging
        # می‌روند تا بعداً به ساختار نهایی auction_number/product_id منتقل شوند.
        staged = orphans = 0
        for directory in sorted(p for p in root.iterdir() if p.is_dir() and has_images(p)):
            if directory.name in ambiguous_codes or directory.name not in code_to_target:
                orphans += 1
                continue
            staged += 1
            if not dry:
                staging.mkdir(exist_ok=True)
                target = staging / directory.name
                if not target.exists():
                    directory.rename(target)

        # مرحله ۲: انتقال از staging به lots/<auction_number>/<product_pk>/
        moved = normalized = 0
        if staging.is_dir() and not dry:
            for directory in sorted(staging.iterdir()):
                target_info = code_to_target.get(directory.name)
                if target_info is None:
                    continue
                auction_dir, product_dir = target_info
                dest = root / auction_dir / product_dir
                dest.mkdir(parents=True, exist_ok=True)
                for f in directory.iterdir():
                    target = dest / f.name
                    if f.is_file() and not target.exists():
                        shutil.move(str(f), str(target))
                        moved += 1
                normalized += normalize_product_directory(dest, dry=dry)
                try:
                    directory.rmdir()
                except OSError:
                    pass
            try:
                staging.rmdir()
            except OSError:
                pass

        for auction_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            for product_dir in sorted(p for p in auction_dir.iterdir() if p.is_dir()):
                normalized += normalize_product_directory(product_dir, dry=dry)

        label = 'DRY-RUN ' if dry else ''
        self.stdout.write(self.style.SUCCESS(
            f'{label}lot folders to move: {staged} | files moved: {moved} | files renamed: {normalized} | '
            f'folders without matching product (left untouched): {orphans}'
        ))
        if ambiguous_codes:
            self.stdout.write(self.style.WARNING(
                f'کد لات تکراری و مبهم: {len(ambiguous_codes)} مورد؛ این پوشه‌ها جابه‌جا نشدند.'
            ))
        
