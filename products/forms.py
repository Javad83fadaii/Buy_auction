from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils import timezone

from .choices import ProductSourceTypeChoices, ProductStatusChoices
from .models import Product
from .validators import validate_product_image

PRODUCT_LIST_DEFAULT_SORT = '-created_at'
PRODUCT_LIST_SORT_CHOICES = (
    ('-created_at', 'جدیدترین'),
    ('created_at', 'قدیمی‌ترین'),
    ('title', 'عنوان A-Z'),
    ('-title', 'عنوان Z-A'),
    ('suitable_price', 'قیمت مناسب کم به زیاد'),
    ('-suitable_price', 'قیمت مناسب زیاد به کم'),
)


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


class ProductCreateForm(forms.ModelForm):
    images = MultipleImageField(
        label='تصاویر اثر',
        required=True,
        widget=MultipleImageInput(
            attrs={
                'accept': '.jpg,.jpeg,.png,.webp',
            }
        ),
        help_text='می‌توانید چند تصویر انتخاب کنید. اولین تصویر انتخاب‌شده به عنوان تصویر اصلی ثبت می‌شود.',
    )

    class Meta:
        model = Product
        fields = (
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
        )
        widgets = {
            'suggested_by': forms.TextInput(attrs={'placeholder': 'نام پیشنهاددهنده'}),
            'contact_method': forms.Select(),
            'suggestion_date': forms.DateInput(attrs={'type': 'date'}),
            'title': forms.TextInput(attrs={'placeholder': 'عنوان اثر'}),
            'product_code': forms.TextInput(attrs={'placeholder': 'کد اثر'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'توضیحات تکمیلی'}),
            'artist': forms.TextInput(attrs={'placeholder': 'نام هنرمند'}),
            'production_date': forms.DateInput(attrs={'type': 'date'}),
            'production_location': forms.TextInput(attrs={'placeholder': 'محل تولید'}),
            'material': forms.TextInput(attrs={'placeholder': 'متریال'}),
            'subject': forms.TextInput(attrs={'placeholder': 'موضوع'}),
            'usage': forms.TextInput(attrs={'placeholder': 'کاربرد'}),
            'art_type': forms.TextInput(attrs={'placeholder': 'نوع هنر'}),
            'suggested_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'suitable_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(self.Meta.fields + ('images',))

        if not self.is_bound:
            self.fields['suggestion_date'].initial = timezone.localdate()

        for name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'checkbox-input')
                continue

            existing_class = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing_class} text-input'.strip()

        self.fields['contact_method'].empty_label = 'انتخاب کنید'
        self.fields['suggested_price'].error_messages['invalid'] = 'مقدار قیمت معتبر نیست.'
        self.fields['suitable_price'].error_messages['invalid'] = 'مقدار قیمت معتبر نیست.'

    def clean_suggested_price(self):
        return self._clean_non_negative_price('suggested_price')

    def clean_suitable_price(self):
        return self._clean_non_negative_price('suitable_price')

    def _clean_non_negative_price(self, field_name):
        value = self.cleaned_data.get(field_name)
        if value is not None and value < 0:
            raise forms.ValidationError('قیمت نمی‌تواند منفی باشد.')
        return value

    def _post_clean(self):
        self.instance.source_type = ProductSourceTypeChoices.MANUAL
        self.instance.status = ProductStatusChoices.DRAFT
        super()._post_clean()
        self._validate_manual_constraints()
        self._move_product_code_duplicate_error()

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

        self.add_error('product_code', 'این کد اثر قبلاً برای پیشنهاد دستی ثبت شده است.')

    def _validate_manual_constraints(self):
        if self.errors:
            return

        try:
            self.instance.validate_constraints()
        except forms.ValidationError as exc:
            self._update_errors(exc)


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing_class} text-input'.strip()

    def clean_sort(self):
        sort = (self.cleaned_data.get('sort') or '').strip()
        allowed_sorts = {value for value, _ in PRODUCT_LIST_SORT_CHOICES}
        if not sort or sort not in allowed_sorts:
            return PRODUCT_LIST_DEFAULT_SORT
        return sort
