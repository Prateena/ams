from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import connection
from django.utils import timezone

from dashboard.models import Artist, Song
from .serializers import ArtistSerializer, SongSerializer

current_datetime = timezone.now()

# Artist List API
class ArtistList(APIView):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE deleted_at IS NULL ORDER BY id")
            artists = dictfetchall(cursor)
        return Response(artists)

# Artist Create API
class ArtistCreateAPIView(generics.CreateAPIView):
    
    def post(self, request):
        data = request.data
        serializer = ArtistSerializer(data=data)

        if serializer.is_valid():
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO dashboard_artist (name, gender, dob, address, no_of_albums_released, first_release_year, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    [data['name'], data['gender'], data['dob'], data['address'], data['no_of_albums_released'], data['first_release_year'], current_datetime, current_datetime]
                )
                cursor.execute("SELECT LASTVAL();")
                artist_id = cursor.fetchone()[0]
                cursor.execute("SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE id = %s AND deleted_at IS NULL", [artist_id])
                artist = dictfetchall(cursor)
            return Response({'artist': artist[0], 'message':'Artist Created Successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Artist Update API
class ArtistUpdateAPIView(generics.UpdateAPIView):

    def update(self, request, *args, **kwargs):
        data = request.data
        serializer = ArtistSerializer(data=data)

        if serializer.is_valid():
            artist_data = serializer.validated_data
            artist_id = self.kwargs.get('pk')  # Get the artist's primary key from the URL
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE dashboard_artist "
                    "SET name=%s, gender=%s, dob=%s, address=%s, no_of_albums_released=%s, first_release_year=%s, updated_at=%s "
                    "WHERE id=%s",
                    [artist_data['name'], artist_data['gender'], artist_data['dob'], artist_data['address'], artist_data['no_of_albums_released'], artist_data['first_release_year'], current_datetime, artist_id]
                )
            return Response({"message": "Artist updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def dictfetchall(cursor):
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]