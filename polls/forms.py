from django import forms
from django.core.exceptions import ValidationError

from . import selectors

MIN_OPTIONS = 2
MAX_OPTIONS = 5
MAX_OPTION_LENGTH = 80
DAILY_POLL_LIMIT = 10


class PollForm(forms.Form):
    question = forms.CharField(
        label="Soru",
        min_length=10,
        max_length=140,
        widget=forms.TextInput(attrs={"maxlength": 140}),
    )
    description = forms.CharField(
        label="Açıklama (opsiyonel)",
        max_length=280,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "maxlength": 280}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        getlist = getattr(self.data, "getlist", None)
        raw_options = getlist("option") if getlist else self.data.get("option", [])
        self.options = [option.strip() for option in raw_options if option.strip()]

    def clean(self):
        cleaned_data = super().clean()

        if len(self.options) < MIN_OPTIONS:
            raise ValidationError(f"En az {MIN_OPTIONS} seçenek gerekli.")
        if len(self.options) > MAX_OPTIONS:
            raise ValidationError(f"En fazla {MAX_OPTIONS} seçenek olabilir.")
        for option in self.options:
            if len(option) > MAX_OPTION_LENGTH:
                raise ValidationError(
                    f"Seçenek metni en fazla {MAX_OPTION_LENGTH} karakter olabilir."
                )
        if len({option.lower() for option in self.options}) != len(self.options):
            raise ValidationError("Seçenekler birbirinden farklı olmalı.")

        if self.user is not None and selectors.count_polls_created_today(self.user) >= DAILY_POLL_LIMIT:
            raise ValidationError(
                f"Bugün en fazla {DAILY_POLL_LIMIT} anket oluşturabilirsin. Yarın tekrar dene."
            )

        return cleaned_data
