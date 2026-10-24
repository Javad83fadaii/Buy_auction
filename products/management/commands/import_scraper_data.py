from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from products.scraper_import import ScraperImportService


class Command(BaseCommand):
    help = 'Import auctions and lots from a scraper database using the shared mapping service.'

    def add_arguments(self, parser):
        parser.add_argument('--scraper-db', default='christies_scraper')
        parser.add_argument('--source-name', default='', help='فقط یک منبع خاص مثل christies یا sothebys')
        parser.add_argument('--limit', type=int, default=0, help='حداکثر تعداد لات (برای تست)')
        parser.add_argument('--batch-size', type=int, default=500)

    def handle(self, *args, **opts):
        try:
            result = ScraperImportService(
                scraper_db=opts['scraper_db'],
                source_name=opts['source_name'],
                limit=opts['limit'],
                batch_size=opts['batch_size'],
            ).run()
        except ValidationError as exc:
            raise CommandError('; '.join(exc.messages)) from exc

        self.stdout.write(self.style.SUCCESS(result.build_summary()))
