from django import forms
from .models import Artist, CustomUser


class FormControlMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class UserForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password', 'phone', 'dob', 'gender', 'address']


class ArtistForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = Artist
        fields = ['name', 'gender', 'dob', 'address', 'no_of_albums_released', 'first_release_year']
