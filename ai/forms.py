from django import forms


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultiFileInput(attrs={"multiple": True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data]
        return [single(data, initial)]


class SlideImageMultiUploadForm(forms.Form):
    images = MultiFileField(
        required=True,
        label="Select images (in click order)",
        help_text="Hold Ctrl/Cmd to select multiple. Files are uploaded in the order shown.",
    )
    title_prefix = forms.CharField(
        required=False,
        label="Title prefix (optional)",
        help_text="e.g. 'Slide' → titles become 'Slide 1', 'Slide 2', ...",
    )
    caption = forms.CharField(
        required=False,
        label="Caption (applied to all)",
        max_length=250,
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Active",
    )