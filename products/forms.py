from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils import timezone

from accounts.constants import OPERATOR_ROLE

from .choices import (
    AuctionHouseChoices,
    AuctionStatusChoices,
    CurrencyChoices,
    ProductSourceTypeChoices,
    ProductStatusChoices,
)
from .models import Auction, Product, ProductImage
from .validators import validate_product_image

User = get_user_model()

PRODUCT_LIST_DEFAULT_SORT = '-created_at'
PRODUCT_LIST_SORT_CHOICES = (
    ('-created_at', 'جدیدترین'),
    ('created_at', 'قدیمی‌ترین'),
    ('title', 'عنوان A-Z'),
    ('-title', 'عنوان Z-A'),
    ('suitable_price', 'قیمت مناسب کم به زیاد'),
    ('-suitable_price', 'قیمت مناسب زیاد به کم'),
)
PRODUCT_IMAGE_ACCEPT_ATTR = '.jpg,.jpeg,.png,.webp'


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError('حداقل یک تصویر الزامی است.')
            return []

        files = data if isinstance(data, (list, tuple)) else [data]
        cleaned_files = []

        for file in files:
            cleaned_file = super().clean(file, initial)
            validate_product_image(cleaned_file)
            cleaned_files.append(cleaned_file)

        return cleaned_files


PRODUCT_EDIT_FIELDS = (
    'auction',
    'suggested_by',
    'contact_method',
    'suggestion_date',
    'title',
    'product_code',
    'description',
    'artist',
    'production_date',
    'production_location',
    'material',
    'subject',
    'usage',
    'art_type',
    'suggested_price',
    'suitable_price',
    'is_cancelled',
    'is_notable',
    'needs_expert_review',
    'assigned_expert',
    'to_buy',
    'has_initial_info',
    'has_all_prices',
    'final_inspection_done',
)


def get_expert_queryset():
    return User.objects.filter(
        is_active=True,
        groups__name=OPERATOR_ROLE,
    ).order_by('first_name', 'last_name', 'username').distinct()


class ProductBaseForm(forms.ModelForm):
    registration_mode = forms.ChoiceField(
        choices=(
            ('manual', 'ثبت پیشنهاد دستی'),
            ('auction', 'ثبت از حراجی خارجی'),
        ),
        initial='manual',
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Product
        fields = ()
        widgets = {
            'auction': forms.Select(),
            'suggested_by': forms.TextInput(attrs={'placeholder': 'نام پیشنهاد دهنده'}),
            'contact_method': forms.Select(),
            'suggestion_date': forms.DateInput(attrs={'type': 'date'}),
            'title': forms.TextInput(attrs={'placeholder': 'عنوان اثر'}),
            'product_code': forms.TextInput(attrs={'placeholder': 'کد اثر'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'توضیحات'}),
            'artist': forms.TextInput(attrs={'placeholder': 'خالق اثر'}),
            'production_date': forms.DateInput(attrs={'type': 'date'}),
            'production_location': forms.TextInput(attrs={'placeholder': 'مکان تولید'}),
            'material': forms.TextInput(attrs={'placeholder': 'متریال'}),
            'subject': forms.TextInput(attrs={'placeholder': 'موضوع'}),
            'usage': forms.TextInput(attrs={'placeholder': 'کاربرد'}),
            'art_type': forms.TextInput(attrs={'placeholder': 'نوع هنر'}),
            'suggested_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'inputmode': 'decimal'}),
            'suitable_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'inputmode': 'decimal'}),
            'assigned_expert': forms.Select(),
        }

    ordered_fields: tuple[str, ...] = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.ordered_fields:
            self.order_fields(self.ordered_fields)

        self._configure_field_labels_and_help_texts()

        if not self.is_bound:
            for field_name, initial_value in self.get_initial_values().items():
                if field_name in self.fields:
                    self.fields[field_name].initial = initial_value

        for name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'checkbox-input')
                continue

            existing_class = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing_class} text-input'.strip()
            widget.attrs.setdefault('dir', 'rtl')

            if isinstance(widget, forms.NumberInput):
                widget.attrs.setdefault('inputmode', 'decimal')
                widget.attrs.setdefault('autocomplete', 'off')

            field.error_messages['required'] = 'این فیلد الزامی است.'

        if 'contact_method' in self.fields:
            contact_method_choices = list(self.fields['contact_method'].choices)
            if contact_method_choices and contact_method_choices[0][0] == '':
                contact_method_choices[0] = ('', 'انتخاب کنید')
                self.fields['contact_method'].choices = contact_method_choices
        if 'suggested_price' in self.fields:
            self.fields['suggested_price'].error_messages['invalid'] = 'مقدار قیمت معتبر نیست.'
        if 'suitable_price' in self.fields:
            self.fields['suitable_price'].error_messages['invalid'] = 'مقدار قیمت معتبر نیست.'
        if 'assigned_expert' in self.fields:
            self.fields['assigned_expert'].queryset = get_expert_queryset()
            self.fields['assigned_expert'].empty_label = 'انتخاب کنید'
        if 'auction' in self.fields:
            self.fields['auction'].queryset = Auction.objects.all().order_by('-start_date', 'name')
            self.fields['auction'].empty_label = 'انتخاب حراجی'

        if self.instance.pk:
            if self.instance.auction_id or self.instance.source_type != ProductSourceTypeChoices.MANUAL:
                self.fields['registration_mode'].initial = 'auction'
            else:
                self.fields['registration_mode'].initial = 'manual'

    def _configure_field_labels_and_help_texts(self):
        field_text_map = {
            'auction': ('حراجی مرتبط', 'حراجی برگزارکننده این اثر را انتخاب کنید.'),
            'title': ('عنوان اثر', 'نام اثر را همان‌طور که باید ثبت شود وارد کنید.'),
            'product_code': ('کد اثر', 'در صورت وجود، کد داخلی یا شناسایی اثر را وارد کنید.'),
            'description': ('توضیحات', 'توضیحات تکمیلی درباره اثر را در صورت نیاز ثبت کنید.'),
            'suggested_price': ('قیمت پیشنهادی', 'مبلغ را بدون جداکننده وارد کنید. پیش‌نمایش عددی در زیر فیلد نمایش داده می‌شود.'),
            'suitable_price': ('قیمت مناسب', 'مبلغ برآوردشده مناسب برای اثر را وارد کنید.'),
            'suggestion_date': ('تاریخ پیشنهاد', 'تاریخ دریافت پیشنهاد را ثبت کنید.'),
            'production_date': ('تاریخ تولید', 'در صورت مشخص بودن، تاریخ تولید اثر را وارد کنید.'),
            'production_location': ('مکان تولید', 'شهر، کشور یا محل تولید اثر را وارد کنید.'),
            'artist': ('خالق اثر', 'نام هنرمند یا خالق اثر را وارد کنید.'),
            'material': ('متریال', 'برای مثال: رنگ روغن روی بوم، برنز، کاغذ و ...'),
            'subject': ('موضوع', 'موضوع یا مضمون اصلی اثر را وارد کنید.'),
            'usage': ('کاربرد', 'کاربری یا زمینه استفاده اثر را ثبت کنید.'),
            'art_type': ('نوع هنر', 'برای مثال: نقاشی، مجسمه، خوشنویسی و ...'),
            'suggested_by': ('نام پیشنهاد دهنده', 'نام شخص یا مجموعه پیشنهاددهنده را وارد کنید.'),
            'contact_method': ('طریقه پیشنهاد', 'روش دریافت این پیشنهاد را انتخاب کنید.'),
            'is_cancelled': ('انصراف', 'اگر پیشنهاد در زمان ثبت انصراف داده شده است این گزینه را فعال کنید.'),
            'is_notable': ('قابل توجه', 'برای آثاری که نیاز به پیگیری بیشتر دارند فعال شود.'),
            'needs_expert_review': ('نیازمند کارشناسی', 'برای آثاری که به بررسی تخصصی نیاز دارند فعال شود.'),
            'assigned_expert': ('ارجاع به کارشناس', 'کارشناس مدنظر را انتخاب کنید. ارجاع نهایی با دکمه اختصاصی ثبت می‌شود.'),
            'to_buy': ('خریداری شود', 'این اثر هدف خرید ما در این حراجی است.'),
            'has_initial_info': ('اطلاعات اولیه وارد شده', 'اطلاعات شناسنامه‌ای و اولیه این اثر تکمیل است.'),
            'has_all_prices': ('تمام قیمت‌ها وارد شده', 'تمام قیمت‌های پایه، برآورد و مناسب تکمیل است.'),
            'final_inspection_done': ('بازدید نهایی شده', 'بازدید فیزیکی و کارشناسی نهایی در محل حراجی انجام شده است.'),
            'images': ('تصاویر اثر', 'می‌توانید چند تصویر انتخاب کنید. اولین تصویر انتخاب‌شده به عنوان تصویر اصلی ثبت می‌شود.'),
        }

        for field_name, (label, help_text) in field_text_map.items():
            if field_name not in self.fields:
                continue
            self.fields[field_name].label = label
            self.fields[field_name].help_text = help_text

    def get_initial_values(self):
        return {}

    def clean_suggested_price(self):
        return self._clean_non_negative_price('suggested_price')

    def clean_suitable_price(self):
        return self._clean_non_negative_price('suitable_price')

    def clean_artist(self):
        val = self.cleaned_data.get('artist') or ''
        return ' '.join(val.split())

    def _clean_non_negative_price(self, field_name):
        value = self.cleaned_data.get(field_name)
        if value is not None and value < 0:
            raise forms.ValidationError('قیمت نمی‌تواند منفی باشد.')
        return value

    def _post_clean(self):
        super()._post_clean()
        self._validate_manual_constraints()
        self._move_product_code_duplicate_error()

    def get_product_code_duplicate_error(self) -> str:
        if self.instance.source_type == ProductSourceTypeChoices.MANUAL:
            return 'این کد اثر قبلاً برای پیشنهاد دستی ثبت شده است.'
        return 'این کد اثر قبلاً برای این منبع ثبت شده است.'

    def _move_product_code_duplicate_error(self):
        product_code = self.cleaned_data.get('product_code')
        if not product_code or NON_FIELD_ERRORS not in self.errors:
            return

        non_field_errors = self.errors.as_data().get(NON_FIELD_ERRORS, [])
        if not any(error.code in {'unique', 'unique_together'} for error in non_field_errors):
            return

        remaining_errors = [
            error.message for error in non_field_errors if error.code not in {'unique', 'unique_together'}
        ]

        if remaining_errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class(remaining_errors)
        else:
            del self._errors[NON_FIELD_ERRORS]

        self.add_error('product_code', self.get_product_code_duplicate_error())

    def _validate_manual_constraints(self):
        if self.errors:
            return

        try:
            self.instance.validate_constraints()
        except forms.ValidationError as exc:
            self._update_errors(exc)


class ProductCreateForm(ProductBaseForm):
    images = MultipleImageField(
        label='تصاویر اثر',
        required=True,
        widget=MultipleImageInput(
            attrs={
                'accept': PRODUCT_IMAGE_ACCEPT_ATTR,
            }
        ),
        help_text='می‌توانید چند تصویر انتخاب کنید. اولین تصویر انتخاب‌شده به عنوان تصویر اصلی ثبت می‌شود.',
    )

    class Meta(ProductBaseForm.Meta):
        fields = PRODUCT_EDIT_FIELDS

    ordered_fields = ('registration_mode',) + Meta.fields + ('images',)

    def get_initial_values(self):
        return {'suggestion_date': timezone.localdate()}

    def _post_clean(self):
        registration_mode = self.cleaned_data.get('registration_mode') or 'manual'
        auction = self.cleaned_data.get('auction')

        if registration_mode == 'auction' or auction is not None:
            if auction:
                if auction.source_house == 'CHRISTIES':
                    self.instance.source_type = ProductSourceTypeChoices.CHRISTIES
                elif auction.source_house == 'SOTHEBYS':
                    self.instance.source_type = ProductSourceTypeChoices.SOTHEBYS
                else:
                    self.instance.source_type = ProductSourceTypeChoices.OTHER_AUCTION
                self.instance.source_name = auction.name
            else:
                self.instance.source_type = ProductSourceTypeChoices.OTHER_AUCTION
        else:
            self.instance.source_type = ProductSourceTypeChoices.MANUAL

        self.instance.status = ProductStatusChoices.PENDING_REVIEW
        super()._post_clean()


class ProductEditForm(ProductBaseForm):
    class Meta(ProductBaseForm.Meta):
        fields = PRODUCT_EDIT_FIELDS

    ordered_fields = ('registration_mode',) + Meta.fields

    def _post_clean(self):
        super()._post_clean()
        registration_mode = self.cleaned_data.get('registration_mode') or 'manual'
        auction = self.cleaned_data.get('auction')
        if registration_mode == 'auction' or auction is not None:
            if auction:
                if auction.source_house == 'CHRISTIES':
                    self.instance.source_type = ProductSourceTypeChoices.CHRISTIES
                elif auction.source_house == 'SOTHEBYS':
                    self.instance.source_type = ProductSourceTypeChoices.SOTHEBYS
                else:
                    self.instance.source_type = ProductSourceTypeChoices.OTHER_AUCTION
                self.instance.source_name = auction.name
            else:
                self.instance.source_type = ProductSourceTypeChoices.OTHER_AUCTION
        else:
            self.instance.source_type = ProductSourceTypeChoices.MANUAL


class ProductImageUploadForm(forms.Form):
    image = forms.FileField(
        label='تصویر',
        widget=forms.ClearableFileInput(
            attrs={
                'accept': PRODUCT_IMAGE_ACCEPT_ATTR,
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing_class = self.fields['image'].widget.attrs.get('class', '')
        self.fields['image'].widget.attrs['class'] = f'{existing_class} text-input'.strip()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        validate_product_image(image)
        return image


class ProductExpertReferralForm(forms.Form):
    expert = forms.ModelChoiceField(
        label='ارجاع به کارشناس',
        queryset=User.objects.none(),
        empty_label='انتخاب کنید',
        widget=forms.Select(),
        error_messages={'required': 'انتخاب کارشناس الزامی است.'},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expert'].queryset = get_expert_queryset()
        existing_class = self.fields['expert'].widget.attrs.get('class', '')
        self.fields['expert'].widget.attrs['class'] = f'{existing_class} text-input'.strip()
        self.fields['expert'].widget.attrs.setdefault('dir', 'rtl')


class ProductImageSortOrderForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ('sort_order',)
        widgets = {
            'sort_order': forms.NumberInput(
                attrs={
                    'min': '0',
                    'inputmode': 'numeric',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing_class = self.fields['sort_order'].widget.attrs.get('class', '')
        self.fields['sort_order'].widget.attrs['class'] = f'{existing_class} text-input'.strip()
        self.fields['sort_order'].error_messages['min_value'] = 'ترتیب نمایش نمی‌تواند منفی باشد.'

    def clean_sort_order(self):
        sort_order = self.cleaned_data.get('sort_order')
        if sort_order is not None and sort_order < 0:
            raise forms.ValidationError('ترتیب نمایش نمی‌تواند منفی باشد.')
        return sort_order


class ProductListFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={'invalid': 'تاریخ شروع معتبر نیست.'},
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={'invalid': 'تاریخ پایان معتبر نیست.'},
    )
    sort = forms.CharField(required=False)
    auction = forms.ModelChoiceField(
        queryset=Auction.objects.none(),
        required=False,
        empty_label='همه حراجی‌ها',
    )
    to_buy = forms.ChoiceField(
        choices=(('all', 'همه آثار'), ('1', 'فقط موارد خرید'), ('0', 'سایر')),
        required=False,
    )
    final_inspection = forms.ChoiceField(
        choices=(('all', 'همه وضعیت‌ها'), ('1', 'بازدید شده'), ('0', 'بازدید نشده')),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['auction'].queryset = Auction.objects.all().order_by('-start_date', 'name')
        for name, field in self.fields.items():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_class} text-input'.strip()

    def clean_sort(self):
        sort = (self.cleaned_data.get('sort') or '').strip()
        allowed_sorts = {value for value, _ in PRODUCT_LIST_SORT_CHOICES}
        if not sort or sort not in allowed_sorts:
            return PRODUCT_LIST_DEFAULT_SORT
        return sort


class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = (
            'name',
            'source_house',
            'start_date',
            'end_date',
            'location',
            'currency',
            'commission_rate',
            'status',
            'total_lots',
            'entered_lots_count',
            'cancelled_lots_count',
            'expert_lots_count',
            'notable_lots_count',
            'to_buy_count',
            'initial_info_count',
            'all_prices_count',
            'final_inspection_count',
        )
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'مثلاً: حراج پاییز ۲۰۲۴ ساتبیز لندن'}),
            'source_house': forms.Select(),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'location': forms.TextInput(attrs={'placeholder': 'مثلاً: لندن، خیابان نیوباند'}),
            'currency': forms.Select(),
            'commission_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': '25.00'}),
            'status': forms.Select(),
            'total_lots': forms.NumberInput(attrs={'min': '0', 'placeholder': 'تعداد کل آثار'}),
            'entered_lots_count': forms.NumberInput(attrs={'min': '0'}),
            'cancelled_lots_count': forms.NumberInput(attrs={'min': '0'}),
            'expert_lots_count': forms.NumberInput(attrs={'min': '0'}),
            'notable_lots_count': forms.NumberInput(attrs={'min': '0'}),
            'to_buy_count': forms.NumberInput(attrs={'min': '0'}),
            'initial_info_count': forms.NumberInput(attrs={'min': '0'}),
            'all_prices_count': forms.NumberInput(attrs={'min': '0'}),
            'final_inspection_count': forms.NumberInput(attrs={'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            existing_class = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing_class} text-input'.strip()
            widget.attrs.setdefault('dir', 'rtl')
            field.error_messages['required'] = 'این فیلد الزامی است.'


class AuctionFilterForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'جستجو در نام، مکان و ...'}))
    source_house = forms.ChoiceField(
        choices=(('', 'همه خانه‌ها'),) + tuple(AuctionHouseChoices.choices),
        required=False,
    )
    status = forms.ChoiceField(
        choices=(('', 'همه وضعیت‌ها'),) + tuple(AuctionStatusChoices.choices),
        required=False,
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_class} text-input'.strip()
