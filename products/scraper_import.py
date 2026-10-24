import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation

import pymysql
from pymysql.cursors import DictCursor, SSDictCursor
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .choices import (
    AuctionHouseChoices,
    AuctionStatusChoices,
    CurrencyChoices,
    ProductSourceTypeChoices,
    ProductStatusChoices,
)
from .models import Auction, Product

NUMBER_RE = re.compile(r'\d[\d,]*(?:\.\d+)?')
CURRENCY_RE = re.compile(r'\b([A-Z]{3})\b')
MAX_PRICE = Decimal('9999999999999999')  # max_digits=18, decimal_places=2

AUCTION_STATUS_MAP = {
    'closed': AuctionStatusChoices.ENDED,
    'live': AuctionStatusChoices.ONGOING,
    'ongoing': AuctionStatusChoices.ONGOING,
    'upcoming': AuctionStatusChoices.UPCOMING,
}
BASE_PRODUCT_UPDATE_FIELDS = (
    'title',
    'description',
    'suggested_price',
    'suitable_price',
    'suggestion_date',
    'source_name',
    'source_url',
    'auction',
    'status',
    'is_cancelled',
)


def normalize_source_name(value: str | None) -> str:
    return str(value or '').strip().lower()


@dataclass(frozen=True)
class BaseScraperMapper:
    source_name: str
    source_label: str
    auction_house: str
    product_source_type: str

    def matches(self, source_name: str) -> bool:
        return normalize_source_name(source_name) == self.source_name

    def build_auction_name(self, row: dict) -> str:
        return (
            row.get('title')
            or row.get('title_fa')
            or row.get('auction_number')
            or row.get('auction_key')
            or f"auction-{row['id']}"
        )[:255]

    def build_auction_number(self, row: dict) -> str:
        return (
            row.get('auction_number')
            or row.get('auction_key')
            or f"auction-{row['id']}"
        )[:128]

    def build_auction_status(self, row: dict) -> str:
        return AUCTION_STATUS_MAP.get(
            normalize_source_name(row.get('status')),
            AuctionStatusChoices.ENDED,
        )

    def build_product_title(self, row: dict) -> str:
        return (row.get('title') or f"Lot {row.get('lot_number') or '-'}")[:255]

    def build_product_description(self, row: dict) -> str:
        return '\n\n'.join(
            part.strip()
            for part in (row.get('description') or '', row.get('lot_essay') or '')
            if part and part.strip()
        )

    def build_is_cancelled(self, row: dict) -> bool:
        return normalize_source_name(row.get('lot_status')) == 'deleted'


class ChristiesScraperMapper(BaseScraperMapper):
    pass


class SothebysScraperMapper(BaseScraperMapper):
    pass


class BonhamsScraperMapper(BaseScraperMapper):
    pass


DEFAULT_SCRAPER_MAPPER = BaseScraperMapper(
    source_name='',
    source_label='سایر منابع',
    auction_house=AuctionHouseChoices.OTHER,
    product_source_type=ProductSourceTypeChoices.OTHER_AUCTION,
)
SCRAPER_MAPPERS = (
    ChristiesScraperMapper(
        source_name='christies',
        source_label="Christie's",
        auction_house=AuctionHouseChoices.CHRISTIES,
        product_source_type=ProductSourceTypeChoices.CHRISTIES,
    ),
    SothebysScraperMapper(
        source_name='sothebys',
        source_label="Sotheby's",
        auction_house=AuctionHouseChoices.SOTHEBYS,
        product_source_type=ProductSourceTypeChoices.SOTHEBYS,
    ),
    BonhamsScraperMapper(
        source_name='bonhams',
        source_label='Bonhams',
        auction_house=AuctionHouseChoices.BONHAMS,
        product_source_type=ProductSourceTypeChoices.OTHER_AUCTION,
    ),
)
SCRAPER_MAPPER_REGISTRY = {mapper.source_name: mapper for mapper in SCRAPER_MAPPERS}
SUPPORTED_SOURCE_CHOICES = (
    ('', 'همه منابع'),
    *((mapper.source_name, mapper.source_label) for mapper in SCRAPER_MAPPERS),
)


def parse_estimate(text):
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


@dataclass
class ScraperImportResult:
    scraper_db: str
    source_name: str = ''
    limit: int = 0
    batch_size: int = 500
    auctions_imported: int = 0
    products_created: int = 0
    products_updated: int = 0
    products_skipped: int = 0
    synced_auction_ids: list[int] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)

    def build_summary(self) -> str:
        source_label = self.source_name or 'همه منابع'
        return (
            f'ایمپورت از دیتابیس «{self.scraper_db}» برای «{source_label}» انجام شد. '
            f'حراجی: {self.auctions_imported} | '
            f'محصول جدید: {self.products_created} | '
            f'محصول به‌روزرسانی‌شده: {self.products_updated} | '
            f'بدون تغییر/تکراری: {self.products_skipped}'
        )


class ScraperImportService:
    def __init__(
        self,
        *,
        scraper_db: str,
        source_name: str = '',
        limit: int = 0,
        batch_size: int = 500,
        user=None,
    ) -> None:
        self.scraper_db = str(scraper_db or '').strip()
        self.source_name = normalize_source_name(source_name)
        self.limit = max(int(limit or 0), 0)
        self.batch_size = max(int(batch_size or 500), 1)
        self.user = user

    def get_mapper(self, source_name: str | None) -> BaseScraperMapper:
        return SCRAPER_MAPPER_REGISTRY.get(normalize_source_name(source_name), DEFAULT_SCRAPER_MAPPER)

    def run(self) -> ScraperImportResult:
        if not self.scraper_db:
            raise ValidationError('نام دیتابیس اسکرپر الزامی است.')

        result = ScraperImportResult(
            scraper_db=self.scraper_db,
            source_name=self.source_name,
            limit=self.limit,
            batch_size=self.batch_size,
        )
        conn = self.connect()
        try:
            auction_map = self.import_auctions(conn)
            result.auctions_imported = len(auction_map)
            self.import_lots(conn, auction_map, result)
        finally:
            conn.close()

        synced_ids = sorted(set(result.synced_auction_ids))
        if synced_ids:
            for auction in Auction.objects.filter(pk__in=synced_ids):
                auction.sync_statistics()
        result.synced_auction_ids = synced_ids
        return result

    def connect(self):
        cfg = settings.DATABASES['default']
        if 'mysql' not in cfg['ENGINE']:
            raise ValidationError('ایمپورت مستقیم از دیتابیس اسکرپر فقط وقتی DB_ENGINE=mysql باشد پشتیبانی می‌شود.')
        return pymysql.connect(
            host=cfg['HOST'] or '127.0.0.1',
            port=int(cfg['PORT'] or 3306),
            user=cfg['USER'],
            password=cfg['PASSWORD'],
            database=self.scraper_db,
            charset='utf8mb4',
        )

    def build_source_filter_sql(self, *, include_where: bool) -> tuple[str, list]:
        if not self.source_name:
            return '', []
        clause = 'WHERE' if include_where else 'AND'
        return f' {clause} source_name = %s', [self.source_name]

    def detect_currency(self, cur, old_auction_id):
        sql = (
            "SELECT estimate_text FROM lots WHERE auction_id = %s "
            "AND estimate_text IS NOT NULL AND estimate_text <> '' LIMIT 50"
        )
        cur.execute(sql, (old_auction_id,))
        counter = Counter()
        for row in cur.fetchall():
            counter.update(CURRENCY_RE.findall(row['estimate_text']))
        if not counter:
            return CurrencyChoices.USD
        code = counter.most_common(1)[0][0]
        return code if code in CurrencyChoices.values else CurrencyChoices.OTHER

    def import_auctions(self, conn):
        auction_map: dict[int, dict[str, int | str]] = {}
        sql = 'SELECT * FROM auctions'
        source_filter_sql, params = self.build_source_filter_sql(include_where=True)
        sql += source_filter_sql
        with conn.cursor(DictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            for row in rows:
                mapper = self.get_mapper(row.get('source_name'))
                name = mapper.build_auction_name(row)
                start = row.get('start_at') or row.get('first_seen_at') or timezone.now()
                defaults = {
                    'auction_number': mapper.build_auction_number(row),
                    'end_date': row['end_at'].date() if row.get('end_at') else None,
                    'location': (row.get('location') or '')[:255],
                    'currency': self.detect_currency(cur, row['id']),
                    'status': mapper.build_auction_status(row),
                    'total_lots': row.get('total_lots') or 0,
                }
                if self.user is not None:
                    defaults['updated_by'] = self.user

                auction, created = Auction.objects.update_or_create(
                    name=name,
                    source_house=mapper.auction_house,
                    start_date=start.date(),
                    defaults=defaults,
                )
                if created and self.user is not None and auction.created_by_id is None:
                    auction.created_by = self.user
                    auction.save(update_fields=['created_by', 'updated_at'])
                auction_map[row['id']] = {
                    'pk': auction.pk,
                    'auction_number': auction.auction_number,
                }
        return auction_map

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

    def build_product_payload(self, row, auction_map):
        low, high = parse_estimate(row.get('estimate_text'))
        suggestion_at = row.get('first_seen_at') or timezone.now()
        source_name = normalize_source_name(row.get('source_name'))
        mapper = self.get_mapper(source_name)
        payload = {
            'title': mapper.build_product_title(row),
            'product_code': self.build_product_code(row, auction_map),
            'description': mapper.build_product_description(row),
            'suggested_price': low,
            'suitable_price': high,
            'suggestion_date': suggestion_at.date(),
            'source_type': mapper.product_source_type,
            'source_name': source_name[:255],
            'source_url': row.get('url') or '',
            'auction_id': (auction_map.get(row['auction_id']) or {}).get('pk'),
            'status': ProductStatusChoices.PENDING_REVIEW,
            'is_cancelled': mapper.build_is_cancelled(row),
        }
        if self.user is not None:
            payload['updated_by'] = self.user
        return payload

    def fetch_existing_products(self, payload_by_key):
        grouped_codes: dict[str, set[str]] = defaultdict(set)
        for source_type, product_code in payload_by_key:
            grouped_codes[source_type].add(product_code)

        filters = Q()
        for source_type, codes in grouped_codes.items():
            filters |= Q(source_type=source_type, product_code__in=list(codes))

        if not filters:
            return {}

        return {
            (product.source_type, product.product_code): product
            for product in Product.objects.filter(filters)
        }

    def flush_products(self, payloads, result: ScraperImportResult):
        if not payloads:
            return

        existing_lookup = self.fetch_existing_products(payloads)
        created_objects = []
        updated_objects = []
        now = timezone.now()
        update_fields = list(BASE_PRODUCT_UPDATE_FIELDS)
        if self.user is not None:
            update_fields.append('updated_by')

        for key, payload in payloads.items():
            existing = existing_lookup.get(key)
            if existing is None:
                if self.user is not None:
                    payload['created_by'] = self.user
                payload['created_at'] = now
                payload['updated_at'] = now
                created_objects.append(Product(**payload))
                continue

            changed = False
            for field_name in update_fields:
                if field_name == 'auction':
                    incoming_value = payload.get('auction_id')
                    target_value = existing.auction_id
                else:
                    incoming_value = payload.get(field_name)
                    target_value = getattr(existing, field_name)
                if target_value != incoming_value:
                    if field_name == 'auction':
                        existing.auction_id = incoming_value
                    else:
                        setattr(existing, field_name, incoming_value)
                    changed = True

            if changed:
                existing.updated_at = now
                updated_objects.append(existing)
            else:
                result.products_skipped += 1

        with transaction.atomic():
            if created_objects:
                Product.objects.bulk_create(created_objects, batch_size=self.batch_size)
            if updated_objects:
                Product.objects.bulk_update(
                    updated_objects,
                    fields=[*update_fields, 'updated_at'],
                    batch_size=self.batch_size,
                )

        result.products_created += len(created_objects)
        result.products_updated += len(updated_objects)

    def import_lots(self, conn, auction_map, result: ScraperImportResult):
        sql = (
            "SELECT source_name, lot_number, url, auction_id, lot_status, title, "
            "estimate_text, description, lot_essay, first_seen_at "
            "FROM lots WHERE page_status = 'ok'"
        )
        params = []
        source_filter_sql, source_params = self.build_source_filter_sql(include_where=False)
        sql += source_filter_sql
        params.extend(source_params)
        sql += ' ORDER BY id'
        if self.limit:
            sql += f' LIMIT {self.limit}'

        batch_rows = []
        with conn.cursor(SSDictCursor) as cur:
            cur.execute(sql, params)
            for row in cur:
                batch_rows.append(row)
                if len(batch_rows) >= self.batch_size:
                    self.flush_rows(batch_rows, auction_map, result)
                    batch_rows = []
            if batch_rows:
                self.flush_rows(batch_rows, auction_map, result)

    def flush_rows(self, rows, auction_map, result: ScraperImportResult):
        payloads = {}
        duplicate_count = 0
        synced_auction_ids = set()

        for row in rows:
            payload = self.build_product_payload(row, auction_map)
            key = (payload['source_type'], payload['product_code'])
            if key in payloads:
                duplicate_count += 1
            payloads[key] = payload
            if payload.get('auction_id'):
                synced_auction_ids.add(payload['auction_id'])

        result.products_skipped += duplicate_count
        result.synced_auction_ids.extend(sorted(synced_auction_ids))
        self.flush_products(payloads, result)
