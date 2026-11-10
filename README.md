خلاصه پروژه buy_auction (برای هوش مصنوعی)

۱. معرفی

buy_auction یک پلتفرم داخلی مدیریت آثار هنری و حراجی‌های خارجی (Christie’s، Sotheby’s، Bonhams و ...) است.
کاربران سیستم ادمین، مدیر، اپراتور و کارشناس هستند.
Stack: Django (حدود 5.x، در یک migration نسخه 6.1 ذکر شده)، MySQL (با fallback به SQLite)، pymysql، Pillow، template سمت سرور (RTL فارسی، فونت Vazirmatn) و Vanilla JS.
ساختار: اپ accounts (کاربر، نقش‌ها، login) و اپ products (Product، ProductImage، Auction، workflow، scraper import). پوشه config شامل settings، urls و StatisticsView است.
Custom User (accounts.User) با فیلد phone_number. نقش‌ها با Django Group پیاده شده‌اند: ADMIN، MANAGER، OPERATOR، EXPERT. دسترسی‌ها در accounts/services.py با ROLE_PERMISSION_BLUEPRINTS تعریف شده و بعد از هر migrate با signal post_migrate دوباره sync می‌شود.

۲. امکانات فعلی

حساب و دسترسی

Login/Logout (POST-only)/تغییر رمز.
ریدایرکت کارشناس فقط به لیست محصولات.
ادمین Django سفارشی با انتخاب نقش، فیلتر نقش و جلوگیری از حذف گروه‌های سیستمی.
is_staff فقط برای نقش ADMIN یا superuser خودکار sync می‌شود.

محصول (Product)

ثبت در دو حالت: «پیشنهاد دستی» (suggested_by، contact_method، تاریخ) و «از حراجی خارجی» (انتخاب Auction).
source_type به‌صورت خودکار از source_house حراجی تعیین می‌شود.
آپلود چند تصویر (jpg/png/webp، حداکثر 5MB، اعتبارسنجی با Pillow). اولین تصویر primary است.
مسیر تصاویر: lots/<auction_number یا manual>/<product_id>/000.ext. thumbnail با فرمت webp در thumbs/.
مدیریت تصویر: آپلود، تعیین primary، تغییر ترتیب، حذف. فایل‌ها بعد از هر تغییر rename/normalize می‌شوند.
پیش‌نمایش قیمت و کمیسیون (Buyer’s Premium) در فرم ثبت.
یکتایی (source_type, product_code).
فیلدهای پیگیری حراجی: to_buy، has_initial_info، has_all_prices، final_inspection_done.

Workflow وضعیت

وضعیت‌ها: DRAFT، PENDING_REVIEW، APPROVED، PUBLISHED، REJECTED، با جدول transition مشخص (WORKFLOW_STATUS_TRANSITIONS).
فقط کاربر با پرمیشن review_product (مدیر/ادمین) می‌تواند approve، reject، publish یا submit_review کند.
مدیر می‌تواند پرچم «قابل توجه»، «نیازمند کارشناسی» و «لغو/فعال‌سازی مجدد» را toggle کند و محصول را به کارشناس ارجاع دهد (assigned_expert).
قفل برای اپراتور: محصول PUBLISHED یا لغوشده را فقط مدیر می‌تواند ویرایش یا لغو کند (can_user_modify_product).
کارشناس فقط محصولات و حراجی‌های ارجاع‌شده به خودش را می‌بیند (is_expert_restricted_user).

لیست، جستجو و صفحات

لیست محصولات: جستجو (عنوان، کد، هنرمند، پیشنهاددهنده)، فیلتر (وضعیت، منبع، حراجی، لغو، to_buy، بازدید نهایی، نوع هنر، بازه تاریخ)، sort سه‌حالته با کلیک روی header و pagination 20تایی.
صفحه جزئیات محصول با gallery و lightbox.
لیست حراجی‌ها با فیلتر.
جزئیات حراجی با جدول آثار.
فرم ثبت و ویرایش حراجی.
آمار حراجی (sync_statistics) هم دستی (دکمه) و هم خودکار هنگام save/delete محصول.
صفحه آمار و گزارشات (/statistics/) و داشبورد.

Import از Scraper

ScraperImportService که هم از UI (فقط superuser) و هم از command import_scraper_data قابل اجراست.
داده خام را از دیتابیس MySQL جداگانه (christies_scraper: جدول‌های auctions و lots) می‌خواند و با mapper هر منبع (Christies/Sothebys/Bonhams) به Auction و Product نگاشت می‌کند.
ارز را از متن estimate تشخیص می‌دهد و با bulk_create/bulk_update در batch ذخیره می‌کند.
Management commands برای تصاویر (به ترتیب اجرا):
organize_lot_images
link_lot_images
make_lot_thumbnails

تست

تست‌های گسترده برای accounts و products (permissions، فرم، لیست، فیلتر، جزئیات، ویرایش، تصاویر، لغو، workflow، حراجی).

۳. مشکلات و باگ‌ها (به ترتیب اهمیت)

مهم

Re-import بازبینی‌ها را بازنویسی می‌کند. BASE_PRODUCT_UPDATE_FIELDS شامل status، is_cancelled، title و description است. اجرای دوباره import، وضعیت APPROVED/PUBLISHED را به PENDING_REVIEW برمی‌گرداند و ویرایش‌های دستی و لغوها را پاک می‌کند.
داشبورد (dashboard.html) پنل‌های تب را هرگز نشان نمی‌دهد. JS دنبال data-dashboard-tab می‌گردد ولی دکمه تب در template وجود ندارد، همه panelها hidden هستند و fallback مقدار all-products هم panel ندارد. لیست آخرین محصولات و حراجی‌ها هیچ‌وقت دیده نمی‌شود.
product_dashboard.html استفاده نمی‌شود و context آن (statistics، recent_products و ...) در هیچ view ساخته نمی‌شود. operator_dashboard.html هم ناقص و قدیمی است و از sidebar جدید استفاده نمی‌کند. دکمه «مدیریت محصولات» در داشبورد به خود داشبورد لینک می‌دهد.
ناسازگاری احتمالی کد اثر در پوشه‌بندی تصاویر. scraper کد را auction_number-lot_number می‌سازد، ولی organize_lot_images پوشه‌ها را با product_code برابر نام پوشه تطبیق می‌دهد (که عملاً فقط lot_number است). ممکن است هیچ پوشه‌ای match نشود (باید بررسی شود). کد در 64 کاراکتر truncate می‌شود و احتمال collision دارد.
طول فیلد image در دیتابیس 100 کاراکتر است (varchar(100))، در حالی که مسیر lots/<auction_number>/<id>/000.jpg با auction_number بلند می‌تواند از آن بیشتر شود. max_length باید بیشتر شود.
فایل buy_auction_before_import.sql در repo است و شامل hash رمز کاربران و session است. باید حذف شود، به .gitignore برود و رمزها عوض شوند. پوشه‌های .vscode و .freebuff هم نباید commit شوند.
ایمپورت scraper از UI همزمان (synchronous) اجرا می‌شود (ریسک timeout برای ده‌ها هزار رکورد). باید با Celery یا background job یا فقط از command انجام شود.

متوسط
8. تنظیمات production ناقص است:

MAILERS یک setting معتبر Django نیست و باید EMAIL_BACKEND باشد.
DEBUG به‌صورت پیش‌فرض True است.
SECURE_*، SESSION_COOKIE_SECURE، CSRF_COOKIE_SECURE، HSTS، logging و CSRF_TRUSTED_ORIGINS تنظیم نشده‌اند.
سرو media/static در production (Nginx/WhiteNoise) تعریف نشده است.
requirements.txt، Dockerfile و README کامل وجود ندارد (README فقط یک خط است).
لیست محصولات تصویر اصلی (full-size) را لود می‌کند (image.url)، نه thumbnail (display_url). تست‌های فعلی هم همین را انتظار دارند و باید به‌روز شوند.
جزئیات حراجی همه آثار را بدون pagination لود می‌کند (همراه با prefetch همه تصاویر). برای حراجی‌های بزرگ کند است.
Product.save() در هر ذخیره، sync_statistics را اجرا می‌کند (8 query، با except Exception: pass که خطا را پنهان می‌کند). وقتی حراجی محصول عوض شود، حراجی قبلی sync نمی‌شود. از طرفی فرم حراجی اجازه ورود دستی شمارنده‌ها را می‌دهد که با sync خودکار تداخل دارد.
صفحه آمار با ده‌ها query جداگانه ساخته می‌شود (.filter().count() در حلقه) و باید با aggregate/annotate بازنویسی شود. منطق فیلتر کارشناس در آن هم عملاً کد مرده است، چون کارشناس پرمیشن add_product ندارد.
پرمیشن‌های حراجی استفاده نمی‌شوند. add_auction/change_auction تعریف شده‌اند ولی view‌ها با add_product/change_product چک می‌کنند. حذف حراجی و حذف محصول در UI وجود ندارد.
لینک «تغییر رمز» فقط برای superuser در sidebar است و برای بقیه نقش‌ها نیست. لینک «داشبورد» هم فقط برای superuser نمایش داده می‌شود، در حالی که مدیر و اپراتور پرمیشن آن را دارند.
ensure_default_roles در هر migrate پرمیشن‌های هر نقش را overwrite می‌کند (permissions.set). تغییر دستی پرمیشن گروه‌ها از ادمین پایدار نیست. signal هم برای هر دو اپ جداگانه اجرا می‌شود.
actionهای ادمین Django با queryset.update workflow را دور می‌زنند (بدون چک transition، بدون updated_by/updated_at).
در product_create.html، داده‌های حراجی مستقیم داخل JS چاپ می‌شوند ({{ a.commission_rate }}). بسته به locale ممکن است اعشار با جداکننده نامناسب چاپ شود و JS بشکند. باید از |unlocalize یا json_script استفاده شود.
شباهت زیاد دو view ProductImageManagement و ProductEdit: در dispatch قبل از چک login، get_object() اجرا می‌شود (برای محصول ناموجود، 404 قبل از redirect به login).
ProductReReviewView و URLهای legacy تکراری (approve/<id>/ و غیره) بدون name.
تکرار منطق: ساخت thumbnail در services.py و command تکرار شده، منطق فیلتر لیست هم هم در ProductListFilterForm و هم در view تکرار شده.
Scraper: suggested_price برابر کران پایین و suitable_price برابر کران بالای estimate است، که از نظر معنایی درست نیست. flagهایی مثل to_buy import نمی‌شوند. کلید update_or_create حراجی (name + house + start_date) با تغییر نام باعث رکورد تکراری می‌شود.

فرانت و UI
22. فونت Vazirmatn از CDN (jsdelivr) با @import لود می‌شود و در شبکه‌ی داخلی یا ایران ممکن است لود نشود. باید لوکال شود. چند @import متوالی CSS هم کند است و بهتر است bundle یا collectstatic شود.
23. دو design system هم‌زمان وجود دارد (آبی در _foundations.css و تک‌رنگ .dash با remap توکن‌ها). دو سیستم دکمه (.button و .dash-btn) و CSS مرده (مثل manager-*، و تعریف تکراری .filter-more summary) هم هست.
24. product_list.html، auction_list.html و صفحات آمار با <style> inline یا <script> inline، body overflow:hidden سراسری می‌گذارند، و JS کلیک ردیف و sort در چند template کپی شده است.
25. تاریخ‌ها میلادی و اعداد لاتین هستند (برای کاربر فارسی بهتر است Jalali با django-jalali و فرمت سه‌رقمی قیمت‌ها اضافه شود). واحد پول محصول دستی در پیش‌نمایش «تومان / ریال» مبهم است.
26. در تست‌ها یک کاراکتر دواناگری اشتباهی در رشته مکان (لंदन) هست. تست‌ها باید دوباره اجرا شوند، چون بعضی با تغییرات اخیر (to_buy، auction، thumbnail) ممکن است قدیمی شده باشند. برای scraper_import، sync آمار، دستورات تصویر و statistics تست کافی وجود ندارد.

۴. کارهایی که باید انجام شود

فوری

رفع باگ re-import (حذف status، is_cancelled و فیلدهای ویرایش‌شده توسط کاربر از update).
رفع تب‌های داشبورد (ساخت دکمه تب یا حذف JS و نمایش مستقیم لیست‌ها).
حذف فایل SQL و .vscode/.freebuff از repo، تغییر رمزها و اضافه کردن به .gitignore.
افزایش max_length فیلد image و thumbnail.
اصلاح EMAIL_BACKEND و ساخت requirements.txt و README کامل.

کوتاه‌مدت

تنظیمات امنیتی production: SECURE_*، cookie secure، HSTS، DEBUG=False، logging، ALLOWED_HOSTS.
استفاده از thumbnail در لیست‌ها.
pagination جزئیات حراجی.
بازنویسی آمار با aggregate.
بررسی و یکسان‌سازی فرمت product_code بین scraper و organize_lot_images.
استفاده از پرمیشن‌های *_auction و اضافه کردن لینک تغییر رمز و داشبورد برای همه نقش‌ها.
فیلتر is_notable و needs_expert_review در لیست محصولات.
لوکال کردن فونت، یکپارچه‌سازی CSS و پاک کردن templateها و CSS مرده.
تکمیل operator_dashboard.html یا حذف آن.
اجرای Import در background (Celery).

فازهای بعدی (طبق برنامه پروژه)

اپ کارشناسی آثار (Expertise): در فایل‌های ارسال‌شده وجود ندارد و طراحی آن جدا انجام شده است.
مدل‌های ExpertAppraisal و DamageAssessment (ForeignKey به Product، چند کارشناسی برای یک اثر).
فرم‌ها و ~20 کلاس TextChoices از فرم کاغذی رسمی.
فیلدهای شرطی بر اساس دسته اثر.
referral_date و appraisal_date.
مرحله بعدی: form، view و template.
QR code: شناسه UUID دائمی و غیرقابل حذف برای هر اثر + صفحه عمومی بدون login (از طریق subdomain، بدون push به سایت mahauction).
راه‌اندازی subdomain و سرور.
اضافه کردن API (DRF) برای مصرف بیرونی، audit log، export Excel/CSV و اعلان‌ها (در صورت نیاز کارفرما).
نکته: buy_auction عمداً جدا از سایت عمومی mahauction نگه داشته شده است.
