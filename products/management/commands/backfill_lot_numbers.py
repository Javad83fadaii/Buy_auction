from collections import defaultdict

import pymysql
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymysql.cursors import DictCursor

from products.models import Product
from products.scraper_import import parse_lot_display_number


class Command(BaseCommand):
    help = 'شماره لات نمایشی محصولات موجود را از دیتابیس اسکرپر پر می‌کند (بدون ساخت محصول تکراری).'

    def add_arguments(self, parser):
        parser.add_argument('--scraper-db', default='christies_scraper')
        parser.add_argument('--batch-size', type=int, default=1000)
        parser.add_argument('--overwrite', action='store_true', help='مقادیر پرشده قبلی را هم دوباره بنویس.')
        parser.add_argument('--dry-run', action='store_true', help='فقط گزارش بده، چیزی ذخیره نکن.')

    def handle(self, *args, **opts):
        by_auction_lot, by_unique_lot = self.build_mapping(opts['scraper_db'])
        self.stdout.write(
            f'نقشه لات‌ها: {len(by_auction_lot)} کلید (مزایده + لات) | {len(by_unique_lot)} لات یکتا'
        )

        updated = skipped = unmatched = 0
        batch = []
        batch_size = max(int(opts['batch_size'] or 1000), 1)

        for product in Product.objects.only('pk', 'product_code', 'lot_display_number').iterator():
            product_prefix, _, lot_number = str(product.product_code or '').strip().rpartition('-')
            lot_number = lot_number.strip()
            display_number = None
            if lot_number:
                display_number = by_auction_lot.get((product_prefix.strip(), lot_number))
                if display_number is None:
                    display_number = by_unique_lot.get(lot_number)

            if display_number is None:
                unmatched += 1
                continue
            if product.lot_display_number == display_number:
                skipped += 1
                continue
            if product.lot_display_number is not None and not opts['overwrite']:
                skipped += 1
                continue

            product.lot_display_number = display_number
            batch.append(product)
            if len(batch) >= batch_size:
                if not opts['dry_run']:
                    Product.objects.bulk_update(batch, ['lot_display_number'], batch_size=batch_size)
                updated += len(batch)
                batch = []

        if batch:
            if not opts['dry_run']:
                Product.objects.bulk_update(batch, ['lot_display_number'], batch_size=batch_size)
            updated += len(batch)

        prefix = 'پیش‌نمایش (بدون ذخیره): ' if opts['dry_run'] else ''
        self.stdout.write(self.style.SUCCESS(
            f'{prefix}شماره لات به‌روزرسانی‌شده: {updated} | بدون تغییر: {skipped} | بدون تطبیق: {unmatched}'
        ))

    def build_mapping(self, scraper_db: str):
        """نقشه (پیشوند شماره مزایده، شماره لات) و نقشه لات‌های بدون ابهام."""
        cfg = settings.DATABASES['default']
        if 'mysql' not in cfg['ENGINE']:
            raise CommandError('این دستور فقط وقتی DB_ENGINE=mysql باشد کار می‌کند.')

        connection = pymysql.connect(
            host=cfg['HOST'] or '127.0.0.1',
            port=int(cfg['PORT'] or 3306),
            user=cfg['USER'],
            password=cfg['PASSWORD'],
            database=scraper_db,
            charset='utf8mb4',
            cursorclass=DictCursor,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT id, auction_number, source_auction_id FROM auctions')
                auction_prefixes = {}
                for row in cursor.fetchall():
                    prefixes = {
                        str(row.get(field) or '').strip()
                        for field in ('auction_number', 'source_auction_id')
                    }
                    auction_prefixes[row['id']] = {value for value in prefixes if value}

                cursor.execute('SELECT lot_number, lot_display_number, auction_id FROM lots')
                lots = cursor.fetchall()
        finally:
            connection.close()

        by_auction_lot: dict[tuple[str, str], int] = {}
        lot_displays: dict[str, set[int]] = defaultdict(set)
        for row in lots:
            lot_number = str(row.get('lot_number') or '').strip()
            display_number = parse_lot_display_number(row.get('lot_display_number'))
            if not lot_number or display_number is None:
                continue
            for prefix in auction_prefixes.get(row.get('auction_id'), ()):
                by_auction_lot[(prefix, lot_number)] = display_number
            lot_displays[lot_number].add(display_number)

        by_unique_lot = {
            lot_number: next(iter(values))
            for lot_number, values in lot_displays.items()
            if len(values) == 1
        }
        return by_auction_lot, by_unique_lot
