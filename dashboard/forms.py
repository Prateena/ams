import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Artist, CustomUser, Song


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Email address is already in use.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\d{10,15}$', phone):
            raise forms.ValidationError("Invalid phone number format. Please enter a valid phone number.")
        return phone


class UserUpdateForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'dob', 'gender', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Email address is already in use.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\d{10,15}$', phone):
            raise forms.ValidationError("Invalid phone number format. Please enter a valid phone number.")
        return phone


class ArtistForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = Artist
        fields = ['name', 'gender', 'dob', 'address', 'no_of_albums_released', 'first_release_year']


class SongForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = Song
        fields = ['title','album_name','genre','release_year']


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label='Import CSV File ')