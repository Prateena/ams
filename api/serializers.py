from rest_framework import serializers
from dashboard.models import Artist, Song

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