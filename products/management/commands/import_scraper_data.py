import re
from collections import Counter
from decimal import Decimal, InvalidOperation

import pymysql
from pymysql.cursors import DictCursor, SSDictCursor
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from products.choices import (
    AuctionHouseChoices,
    AuctionStatusChoices,
    CurrencyChoices,
    ProductSourceTypeChoices,
    ProductStatusChoices,
)
from products.models import Auction, Product

HOUSE_MAP = {
    'christies': AuctionHouseChoices.CHRISTIES,
    'sothebys': AuctionHouseChoices.SOTHEBYS,
    'bonhams': AuctionHouseChoices.BONHAMS,
}
SOURCE_TYPE_MAP = {
    'christies': ProductSourceTypeChoices.CHRISTIES,
    'sothebys': ProductSourceTypeChoices.SOTHEBYS,
}
AUCTION_STATUS_MAP = {
    'closed': AuctionStatusChoices.ENDED,
    'live': AuctionStatusChoices.ONGOING,
    'upcoming': AuctionStatusChoices.UPCOMING,
}
NUMBER_RE = re.compile(r'\d[\d,]*(?:\.\d+)?')
CURRENCY_RE = re.compile(r'\b([A-Z]{3})\b')
MAX_PRICE = Decimal('9999999999999999')  # max_digits=18, decimal_places=2


def parse_estimate(text):
    """'USD 5,000 - 7,000' -> (5000, 7000)"""
    values = []
    for raw in NUMBER_RE.findall(text or ''):
        try:
            value = Decimal(raw.replace(',', ''))
        except InvalidOperation:
            continue
        if value <= MAX_PRICE:
            values.append(value)
    low = values[0] if values else None
    high = values[1] if len(values) > 1 else None
    return low, high


class Command(BaseCommand):
    help = 'Import auctions and lots from the christies_scraper database.'

    def add_arguments(self, parser):
        parser.add_argument('--scraper-db', default='christies_scraper')
        parser.add_argument('--limit', type=int, default=0, help='حداکثر تعداد لات (برای تست)')
        parser.add_argument('--batch-size', type=int, default=500)

    def connect(self, db_name):
        cfg = settings.DATABASES['default']
        if 'mysql' not in cfg['ENGINE']:
            raise CommandError('این command فقط برای DB_ENGINE=mysql نوشته شده است.')
        return pymysql.connect(
            host=cfg['HOST'] or '127.0.0.1',
            port=int(cfg['PORT'] or 3306),
            user=cfg['USER'],
            password=cfg['PASSWORD'],
            database=db_name,
            charset='utf8mb4',
        )

    def handle(self, *args, **opts):
        conn = self.connect(opts['scraper_db'])
        try:
            auction_map = self.import_auctions(conn)
            self.import_lots(conn, auction_map, opts['limit'], opts['batch_size'])
        finally:
            conn.close()

        for auction in Auction.objects.filter(
            pk__in=[auction_data['pk'] for auction_data in auction_map.values()]
        ):
            auction.sync_statistics()
        self.stdout.write(self.style.SUCCESS('Done.'))

    # ---------- auctions ----------
    def detect_currency(self, cur, old_auction_id):
        cur.execute(
            "SELECT estimate_text FROM lots WHERE auction_id = %s "
            "AND estimate_text IS NOT NULL AND estimate_text <> '' LIMIT 50",
            (old_auction_id,),
        )
        counter = Counter()
        for row in cur.fetchall():
            counter.update(CURRENCY_RE.findall(row['estimate_text']))
        if not counter:
            return CurrencyChoices.USD
        code = counter.most_common(1)[0][0]
        return code if code in CurrencyChoices.values else CurrencyChoices.OTHER

    def import_auctions(self, conn):
        auction_map = {}  # old id -> {'pk': new Auction pk, 'auction_number': value}
        with conn.cursor(DictCursor) as cur:
            cur.execute('SELECT * FROM auctions')
            rows = cur.fetchall()
            for row in rows:
                name = (
                    row['title'] or row['title_fa'] or row['auction_number'] or row['auction_key']
                )[:255]
                start = row['start_at'] or row['first_seen_at']
                house = HOUSE_MAP.get(row['source_name'], AuctionHouseChoices.OTHER)
                defaults = {
                    'auction_number': (row['auction_number'] or row['auction_key'] or '')[:128],
                    'end_date': row['end_at'].date() if row['end_at'] else None,
                    'location': (row['location'] or '')[:255],
                    'currency': self.detect_currency(cur, row['id']),
                    'status': AUCTION_STATUS_MAP.get(
                        (row['status'] or '').lower(), AuctionStatusChoices.ENDED
                    ),
                    'total_lots': row['total_lots'] or 0,
                }
                auction, _ = Auction.objects.update_or_create(
                    name=name,
                    source_house=house,
                    start_date=start.date(),
                    defaults=defaults,
                )
                auction_map[row['id']] = {
                    'pk': auction.pk,
                    'auction_number': auction.auction_number,
                }
        self.stdout.write(f'Auctions imported: {len(auction_map)}')
        return auction_map

    # ---------- lots ----------
    def build_product_code(self, row, auction_map):
        auction_data = auction_map.get(row['auction_id']) or {}
        auction_number = str(auction_data.get('auction_number') or '').strip()
        lot_number = str(row.get('lot_number') or '').strip()

        if auction_number and lot_number:
            return f'{auction_number}-{lot_number}'[:64]
        if lot_number:
            return lot_number[:64]
        if auction_number:
            return auction_number[:64]
        return f"auction-{row['auction_id']}-lot"[:64]

    def build_product(self, row, auction_map):
        low, high = parse_estimate(row['estimate_text'])
        description = '\n\n'.join(p for p in (row['description'], row['lot_essay']) if p)
        return Product(
            title=(row['title'] or f"Lot {row['lot_number']}")[:255],
            product_code=self.build_product_code(row, auction_map),
            description=description,
            suggested_price=low,
            suitable_price=high,
            suggestion_date=row['first_seen_at'].date(),
            source_type=SOURCE_TYPE_MAP.get(row['source_name'], ProductSourceTypeChoices.OTHER_AUCTION),
            source_url=row['url'],
            auction_id=(auction_map.get(row['auction_id']) or {}).get('pk'),
            status=ProductStatusChoices.PENDING_REVIEW,
            is_cancelled=(row['lot_status'] or '').lower() == 'deleted',
        )

    def import_lots(self, conn, auction_map, limit, batch_size):
        sql = (
            "SELECT source_name, lot_number, url, auction_id, lot_status, title, "
            "estimate_text, description, lot_essay, first_seen_at "
            "FROM lots WHERE page_status = 'ok' ORDER BY id"
        )
        if limit:
            sql += f' LIMIT {int(limit)}'

        batch, total = [], 0
        with conn.cursor(SSDictCursor) as cur:
            cur.execute(sql)
            for row in cur:
                batch.append(self.build_product(row, auction_map))
                if len(batch) >= batch_size:
                    total += self.flush(batch)
                    batch = []
                    self.stdout.write(f'  processed {total}')
            if batch:
                total += self.flush(batch)
        self.stdout.write(f'Lots processed: {total}')

    def flush(self, batch):
        with transaction.atomic():
            Product.objects.bulk_create(batch, ignore_conflicts=True)
        return len(batch)
