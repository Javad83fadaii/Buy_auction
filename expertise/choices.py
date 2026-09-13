from django.db import models


class LoanTypeChoices(models.TextChoices):
    LOANED = 'LOANED', 'امانی'
    INTERNAL = 'INTERNAL', 'داخلی'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class ArtworkTypeChoices(models.TextChoices):
    MANUSCRIPT_BOOK = 'MANUSCRIPT_BOOK', 'کتاب خطی'
    LITHOGRAPH_BOOK = 'LITHOGRAPH_BOOK', 'کتاب چاپ سنگی'
    MANUSCRIPT_FOLIO = 'MANUSCRIPT_FOLIO', 'قطعه خطی'
    PAINTING = 'PAINTING', 'تابلو نقاشی'
    MINIATURE = 'MINIATURE', 'قطعه مینیاتور'
    ILLUMINATION = 'ILLUMINATION', 'قطعه تذهیب'
    PAPIER_MACHE_PENCASE = 'PAPIER_MACHE_PENCASE', 'قلمدان پاپیه ماشه'
    ASTROLABE = 'ASTROLABE', 'اسطرلاب'
    METAL_GLOBE = 'METAL_GLOBE', 'کره زمین فلزی'
    CARPET = 'CARPET', 'فرش'
    HANDWOVEN = 'HANDWOVEN', 'دست بافت'
    QALAMKAR_FABRIC = 'QALAMKAR_FABRIC', 'پارچه قلمکار'
    METAL_ARTIFACT = 'METAL_ARTIFACT', 'مصنوعات فلزی'
    PHOTOGRAPH = 'PHOTOGRAPH', 'عکس'
    JEWELRY = 'JEWELRY', 'زیورآلات'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class ContentSubjectChoices(models.TextChoices):
    QURAN = 'QURAN', 'قرآن'
    PRAYERS = 'PRAYERS', 'ادعیه'
    ASTRONOMY = 'ASTRONOMY', 'نجوم'
    MEDICINE = 'MEDICINE', 'پزشکی'
    POETRY = 'POETRY', 'شعر'
    PHILOSOPHY = 'PHILOSOPHY', 'فلسفه'
    HISTORY = 'HISTORY', 'تاریخ'
    GEOGRAPHY = 'GEOGRAPHY', 'جغرافیا'
    GENEALOGY = 'GENEALOGY', 'احراز'
    BIBLE = 'BIBLE', 'انجیل'
    TORAH = 'TORAH', 'تورات'
    MYSTICISM = 'MYSTICISM', 'عرفان'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class CalendarTypeChoices(models.TextChoices):
    SHAMSI = 'SHAMSI', 'هجری شمسی'
    QAMARI = 'QAMARI', 'هجری قمری'
    MILADI = 'MILADI', 'میلادی'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class HistoricalMatchChoices(models.TextChoices):
    CONFIRMED = 'CONFIRMED', 'تایید می‌شود'
    PROBABLE = 'PROBABLE', 'احتمالی'
    REJECTED = 'REJECTED', 'مردود'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class AttributionCertaintyChoices(models.TextChoices):
    DEFINITE = 'DEFINITE', 'قطعی'
    ATTRIBUTED = 'ATTRIBUTED', 'منسوب'
    PROBABLE = 'PROBABLE', 'احتمالی'
    UNKNOWN = 'UNKNOWN', 'ناشناس'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class LanguageChoices(models.TextChoices):
    PERSIAN = 'PERSIAN', 'فارسی'
    ARABIC = 'ARABIC', 'عربی'
    LATIN = 'LATIN', 'لاتین'
    HEBREW = 'HEBREW', 'عبری'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class ScriptChoices(models.TextChoices):
    TALIQ = 'TALIQ', 'تعلیق'
    RIQA = 'RIQA', 'رقاع'
    REYHAN = 'REYHAN', 'ریحان'
    TAWQI = 'TAWQI', 'توقیع'
    THULUTH = 'THULUTH', 'ثلث'
    NASKH = 'NASKH', 'نسخ'
    KUFI_EASTERN = 'KUFI_EASTERN', 'کوفی مشرقی'
    KUFI_WESTERN = 'KUFI_WESTERN', 'کوفی مغربی'
    KUFI_EARLY = 'KUFI_EARLY', 'کوفی مبکر'
    SHEKASTE_NASTALIQ = 'SHEKASTE_NASTALIQ', 'شکسته نستعلیق'
    DIVANI = 'DIVANI', 'دیوانی'
    OBSOLETE_SCRIPTS = 'OBSOLETE_SCRIPTS', 'خطوط منسوخ شده'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class MaterialChoices(models.TextChoices):
    PAPER = 'PAPER', 'کاغذ'
    PARCHMENT = 'PARCHMENT', 'پوست'
    SILK = 'SILK', 'ابریشم'
    LINEN = 'LINEN', 'کتان'
    BRASS = 'BRASS', 'برنج'
    SILVER = 'SILVER', 'نقره'
    PAPIER_MACHE = 'PAPIER_MACHE', 'پاپیه ماشه'
    WOOL_CASHMERE = 'WOOL_CASHMERE', 'پشم/کرک'
    STEEL = 'STEEL', 'فولاد'
    WOOD = 'WOOD', 'چوب'
    GLASS = 'GLASS', 'شیشه'
    MIRROR = 'MIRROR', 'آینه'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class InkTypeChoices(models.TextChoices):
    GOLD = 'GOLD', 'طلا نویسی'
    COLORED = 'COLORED', 'رنگین نویسی'
    BLACK = 'BLACK', 'مرکب سیاه'
    LAPIS = 'LAPIS', 'لاجورد'
    WHITE_LEAD = 'WHITE_LEAD', 'سفیدآب'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class IlluminationTechniqueChoices(models.TextChoices):
    HALKARI = 'HALKARI', 'حلکاری'
    TASHIR = 'TASHIR', 'تشعیر'
    TOOTH_CARVING = 'TOOTH_CARVING', 'دندان موشی'
    PARDAZ = 'PARDAZ', 'پرداز'
    MOHARAR = 'MOHARAR', 'محرر'
    SIAH_GHALAM = 'SIAH_GHALAM', 'سیاه قلم'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class PaintingTypeChoices(models.TextChoices):
    FLOWER_BIRD = 'FLOWER_BIRD', 'گل و مرغ'
    ESLIMI = 'ESLIMI', 'اسلیمی'
    KHATAYI = 'KHATAYI', 'خطایی'
    LACHAK_TORANJ = 'LACHAK_TORANJ', 'لچک و ترنج'
    MINIATURE = 'MINIATURE', 'مینیاتور'
    HALKARI = 'HALKARI', 'حلکاری'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class CoverTypeChoices(models.TextChoices):
    MOROCCO_LEATHER = 'MOROCCO_LEATHER', 'چرم میشن'
    SAGHRI_LEATHER = 'SAGHRI_LEATHER', 'چرم ساغری'
    COWHIDE_LEATHER = 'COWHIDE_LEATHER', 'چرم گاوی'
    PYROGRAPHY = 'PYROGRAPHY', 'سوختکاری'
    PYROGRAPHY_INLAY = 'PYROGRAPHY_INLAY', 'سوخت معرق'
    LACQUER = 'LACQUER', 'جلد لاکی'
    WOODEN = 'WOODEN', 'چوبی'
    GILDED_LEATHER = 'GILDED_LEATHER', 'چرم طلاکاری/سوخت'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class WarpWeftMaterialChoices(models.TextChoices):
    SILK = 'SILK', 'ابریشم'
    CASHMERE = 'CASHMERE', 'کرک'
    WOOL = 'WOOL', 'پشم'
    COTTON = 'COTTON', 'پنبه'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class FabricTypeChoices(models.TextChoices):
    SILK = 'SILK', 'ابریشم'
    BROCADE = 'BROCADE', 'زربافت'
    CALICO = 'CALICO', 'متقال'
    VELVET = 'VELVET', 'مخمل'
    COTTON = 'COTTON', 'پنبه'
    PAISLEY = 'PAISLEY', 'بته جقه'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class KnotTypeChoices(models.TextChoices):
    DOUBLE = 'DOUBLE', 'جفتی'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class DesignPatternChoices(models.TextChoices):
    LACHAK_TORANJ = 'LACHAK_TORANJ', 'لچک ترنج'
    FISH_PATTERN = 'FISH_PATTERN', 'نقشه ماهی'
    BIBI_BAFT = 'BIBI_BAFT', 'بی‌بی بافت'
    AROOS_BAFT = 'AROOS_BAFT', 'عروس بافت'
    LEILI_MAJNUN = 'LEILI_MAJNUN', 'لیلی مجنون'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class HealthStatusChoices(models.TextChoices):
    MINOR_DAMAGE = 'MINOR_DAMAGE', 'آسیب جزئی'
    FULL_HEALTH = 'FULL_HEALTH', 'سلامت کامل'
    SEVERE_RISK = 'SEVERE_RISK', 'در معرض آسیب جدی'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'


class DamageTypeChoices(models.TextChoices):
    STAIN = 'STAIN', 'لکه'
    DISCOLORATION = 'DISCOLORATION', 'تغییر رنگ'
    TEAR = 'TEAR', 'پارگی'
    CORROSION = 'CORROSION', 'خوردگی'
    CRACK = 'CRACK', 'ترک'
    MOISTURE = 'MOISTURE', 'رطوبت'
    MOLD = 'MOLD', 'کپک'
    INSECT_DAMAGE = 'INSECT_DAMAGE', 'آسیب حشرات'
    DETACHMENT = 'DETACHMENT', 'افتادگی/جداشدگی'
    FRAME_DAMAGE = 'FRAME_DAMAGE', 'آسیب قاب'
    MISSING_PARTS = 'MISSING_PARTS', 'نقص قطعات'
    OTHER = 'OTHER', 'دیگر'


class FinalVerdictChoices(models.TextChoices):
    AUCTION_READY = 'AUCTION_READY', 'قابل عرضه در حراج'
    NOT_SUITABLE = 'NOT_SUITABLE', 'غیر قابل عرضه'
    NEEDS_FURTHER_REVIEW = 'NEEDS_FURTHER_REVIEW', 'نیازمند بررسی بیشتر'
    OTHER = 'OTHER', 'دیگر'
    NONE = 'NONE', 'هیچ‌کدام'