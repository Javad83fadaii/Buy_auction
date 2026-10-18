from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.management.base import BaseCommand

from products.models import Product, ProductImage

ALLOWED = {'.jpg', '.jpeg', '.png', '.webp'}


def sort_key(f: Path):
    return (0, int(f.stem)) if f.stem.isdigit() else (1, f.stem)


class Command(BaseCommand):
    help = 'Link images in media/lots/<auction_number>/<product_pk>/<position>.<ext> to products.'

    def add_arguments(self, parser):
        parser.add_argument('--folder', default='lots')
        parser.add_argument('--batch-size', type=int, default=1000)

    def handle(self, *args, **opts):
        folder = opts['folder']
        root = Path(settings.MEDIA_ROOT) / folder
        if not root.is_dir():
            self.stderr.write(f'Folder not found: {root}')
            return

        product_lookup = {
            (product.get_image_directory_name(), str(product.pk)): product.pk
            for product in Product.objects.filter(auction__isnull=False).select_related('auction').iterator()
        }
        existing_paths = set(ProductImage.objects.values_list('image', flat=True))
        has_primary = set(
            ProductImage.objects.filter(is_primary=True).values_list('product_id', flat=True)
        )

        batch, created, missing, legacy = [], 0, 0, 0
        for auction_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            for product_dir in auction_dir.iterdir():
                if not product_dir.is_dir():
                    legacy += 1  # فایل مستقیم داخل پوشه حراجی = ساختار قدیمی
                    continue

                product_pk = product_lookup.get((auction_dir.name, product_dir.name))
                if product_pk is None:
                    missing += 1
                    continue

                files = sorted(
                    (f for f in product_dir.iterdir() if f.suffix.lower() in ALLOWED),
                    key=sort_key,
                )
                assigned_primary_in_batch = product_pk in has_primary
                for index, f in enumerate(files):
                    rel_path = str(
                        PurePosixPath(folder) / auction_dir.name / product_dir.name / f.name
                    )
                    if rel_path in existing_paths:
                        continue
                    sort_order = int(f.stem) if f.stem.isdigit() else index
                    is_primary = False
                    if not assigned_primary_in_batch and (sort_order == 0 or index == 0):
                        is_primary = True
                    batch.append(
                        ProductImage(
                            product_id=product_pk,
                            image=rel_path,
                            is_primary=is_primary,
                            sort_order=sort_order,
                        )
                    )
                    if is_primary:
                        assigned_primary_in_batch = True
                        has_primary.add(product_pk)

                if len(batch) >= opts['batch_size']:
                    ProductImage.objects.bulk_create(batch)
                    created += len(batch)
                    batch = []

        if batch:
            ProductImage.objects.bulk_create(batch)
            created += len(batch)

        self.stdout.write(self.style.SUCCESS(
            f'Images linked: {created} | product folders without matching product: {missing}'
        ))
        if legacy:
            self.stdout.write(self.style.WARNING(
                f'{legacy} فایل در ساختار قدیمی پیدا شد؛ ابتدا organize_lot_images را اجرا کن.'
            ))
            
