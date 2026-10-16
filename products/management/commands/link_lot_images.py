from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from products.choices import ProductSourceTypeChoices
from products.models import Product, ProductImage

ALLOWED = {'.jpg', '.jpeg', '.png', '.webp'}


class Command(BaseCommand):
    help = 'Link images in media/lots/<lot_number>/<position>.<ext> to products.'

    def add_arguments(self, parser):
        parser.add_argument('--folder', default='lots')
        parser.add_argument('--source', default=ProductSourceTypeChoices.CHRISTIES)
        parser.add_argument('--batch-size', type=int, default=1000)

    def handle(self, *args, **opts):
        root = Path(settings.MEDIA_ROOT) / opts['folder']
        if not root.is_dir():
            self.stderr.write(f'Folder not found: {root}')
            return

        code_to_pk = dict(
            Product.objects.filter(source_type=opts['source'])
            .values_list('product_code', 'pk')
        )
        existing_paths = set(ProductImage.objects.values_list('image', flat=True))
        products_with_images = set(ProductImage.objects.values_list('product_id', flat=True))

        batch, created, missing = [], 0, 0
        for lot_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            product_pk = code_to_pk.get(lot_dir.name)
            if product_pk is None:
                missing += 1
                continue

            files = [f for f in lot_dir.iterdir() if f.suffix.lower() in ALLOWED]
            files.sort(key=lambda f: (0, int(f.stem)) if f.stem.isdigit() else (1, f.stem))

            has_primary = product_pk in products_with_images
            for index, f in enumerate(files):
                rel_path = f'{opts["folder"]}/{lot_dir.name}/{f.name}'
                if rel_path in existing_paths:
                    continue
                order = int(f.stem) if f.stem.isdigit() else index
                batch.append(
                    ProductImage(
                        product_id=product_pk,
                        image=rel_path,
                        is_primary=(not has_primary and index == 0),
                        sort_order=order,
                    )
                )
                if index == 0:
                    has_primary = True

            if len(batch) >= opts['batch_size']:
                ProductImage.objects.bulk_create(batch)
                created += len(batch)
                batch = []

        if batch:
            ProductImage.objects.bulk_create(batch)
            created += len(batch)

        self.stdout.write(self.style.SUCCESS(
            f'Images linked: {created} | folders without matching product: {missing}'
        ))