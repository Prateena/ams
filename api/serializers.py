import re

from rest_framework import serializers

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import connection

from dashboard.models import Artist, Song, CustomUser

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=255)
    ams_token = serializers.CharField(required=False)

    def validate(self, data):
        request = self.context.get('request')
        user = authenticate(request, username=data.get('username'), password=data.get('password'))
        if user:
            validated_data = super().validate(data)
            validated_data.update({'user':user})
            return validated_data
        raise serializers.ValidationError('Username or Password incorrect!!')
    
def is_valid_email(email):
    # Perform a raw SQL query to check if the email already exists in the database
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM dashboard_customuser WHERE email = %s", [email])
        count = cursor.fetchone()[0]

    return count == 0

class RegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['first_name','last_name','email','password','phone','dob','gender','address']

    def validate_email(self, value):
        email = value
        if not is_valid_email(email):
            raise serializers.ValidationError("Please enter a valid and unique email address.")
        return email
    
    def validate_phone(self, value):
        phone = value
        if not re.match(r'^\d{10,15}$', phone):
            raise serializers.ValidationError("Invalid phone number format. Please enter a valid phone number.")
        return phone
    
class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()

    class Meta:
        model = CustomUser
        fields = ['first_name','last_name','email','phone','dob','gender','address']

    def validate_email(self, value):
        email = value
        if not is_valid_email(email):
            raise serializers.ValidationError("Please enter a valid and unique email address.")
        return email
    
    def validate_phone(self, value):
        phone = value
        if not re.match(r'^\d{10,15}$', phone):
            raise serializers.ValidationError("Invalid phone number format. Please enter a valid phone number.")
        return phone

    
class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ['id','name','gender','dob','address','first_release_year','no_of_albums_released']

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = ['id','title','album_name','genre','release_year']

class ArtistDetailSerializer(serializers.ModelSerializer):
    songs = SongSerializer(many=True)

    class Meta:
        model = Artist
        fields = ['id','name','gender','dob','address','first_release_year','no_of_albums_released','songs']

class CSVImportSerializer(serializers.Serializer):
    csv_file = serializers.FileField(required=True)