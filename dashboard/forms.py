import re

from django import forms
from django.db import connection

from .models import Artist, CustomUser, Song


class FormControlMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


def is_valid_email(email):
    # Perform a raw SQL query to check if the email already exists in the database
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM dashboard_customuser WHERE email = %s", [email])
        count = cursor.fetchone()[0]

    return count == 0

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
        email = self.cleaned_data['email']
        if not is_valid_email(email):
            raise forms.ValidationError("Please enter a valid and unique email address.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\d{10,15}$', phone):
            raise forms.ValidationError("Invalid phone number format. Please enter a valid phone number.")
        return phone
    

def is_valid_email_update(email, current_user_id):
    # Perform a raw SQL query to check if the email already exists in the database for other users
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM dashboard_customuser WHERE email = %s AND id != %s", [email, current_user_id])
        count = cursor.fetchone()[0]

    return count == 0

class UserUpdateForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'dob', 'gender', 'address']

    def __init__(self, current_user, *args, **kwargs):
        self.current_user = current_user
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data['email']
        if not is_valid_email_update(email, self.current_user[0]):
            raise forms.ValidationError("Please enter a valid and unique email address.")
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