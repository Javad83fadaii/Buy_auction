from django.db import models


class ContactMethodChoices(models.TextChoices):
    WHATSAPP = 'WHATSAPP', 'واتساپ'
    TELEGRAM = 'TELEGRAM', 'تلگرام'
    EITAA = 'EITAA', 'ایتا'
    PHONE = 'PHONE', 'تلفن'
    IN_PERSON = 'IN_PERSON', 'حضوری'
    WEBSITE = 'WEBSITE', 'وب‌سایت'
    OTHER = 'OTHER', 'سایر'


class ProductSourceTypeChoices(models.TextChoices):
    MANUAL = 'MANUAL', 'پیشنهاد دستی'
    CHRISTIES = 'CHRISTIES', "Christie's"
    SOTHEBYS = 'SOTHEBYS', "Sotheby's"
    OTHER_AUCTION = 'OTHER_AUCTION', 'سایر حراجی‌ها'


class ProductStatusChoices(models.TextChoices):
    DRAFT = 'DRAFT', 'پیش‌نویس'
    PENDING_REVIEW = 'PENDING_REVIEW', 'در انتظار بررسی'
    APPROVED = 'APPROVED', 'تأیید شده'
    PUBLISHED = 'PUBLISHED', 'منتشر شده'
    REJECTED = 'REJECTED', 'رد شده'


class AuctionHouseChoices(models.TextChoices):
    CHRISTIES = 'CHRISTIES', "Christie's"
    SOTHEBYS = 'SOTHEBYS', "Sotheby's"
    BONHAMS = 'BONHAMS', "Bonhams"
    OTHER = 'OTHER', 'سایر حراجی‌ها'


class AuctionStatusChoices(models.TextChoices):
    UPCOMING = 'UPCOMING', 'به زودی'
    ONGOING = 'ONGOING', 'در حال برگزاری'
    ENDED = 'ENDED', 'پایان یافته'


class CurrencyChoices(models.TextChoices):
    USD = 'USD', 'دلار آمریکا (USD)'
    EUR = 'EUR', 'یورو (EUR)'
    GBP = 'GBP', 'پوند انگلیس (GBP)'
    AED = 'AED', 'درهم امارات (AED)'
    IRR = 'IRR', 'ریال ایران (IRR)'
    OTHER = 'OTHER', 'سایر'
