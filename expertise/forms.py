from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .models import ExpertAppraisal, get_artist_or_scribe_names


class ArtistOrScribeDatalistWidget(forms.TextInput):
    """
    A responsive, accessible text input with an HTML5 datalist autocomplete.
    Allows free-form typing for new artists/scribes, while offering instant
    suggestions for existing names in the database.
    """
    def __init__(self, datalist_id=None, attrs=None):
        widget_attrs = {'autocomplete': 'off'}
        if attrs:
            widget_attrs.update(attrs)
        super().__init__(attrs=widget_attrs)
        self.datalist_id = datalist_id

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        input_id = attrs.get('id') or f'id_{name}'
        datalist_id = self.datalist_id or f'{input_id}_list'
        render_attrs = dict(attrs)
        render_attrs['list'] = datalist_id

        text_input_html = super().render(name, value, render_attrs, renderer)
        try:
            names = get_artist_or_scribe_names()
        except Exception:
            names = []

        options = '\n'.join(f'  <option value="{escape(item)}">' for item in names if item)
        datalist_html = f'<datalist id="{datalist_id}">\n{options}\n</datalist>'
        return mark_safe(f'{text_input_html}\n{datalist_html}')


class ExpertAppraisalAdminForm(forms.ModelForm):
    class Meta:
        model = ExpertAppraisal
        fields = '__all__'
        widgets = {
            'artist_or_scribe_name': ArtistOrScribeDatalistWidget(
                attrs={
                    'placeholder': 'نام هنرمند یا کاتب را انتخاب یا تایپ کنید...',
                    'style': 'width: 100%; max-width: 25rem;',
                }
            ),
        }

    def clean_artist_or_scribe_name(self):
        val = self.cleaned_data.get('artist_or_scribe_name') or ''
        return ' '.join(val.split())
