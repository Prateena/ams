from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import connection
from django.utils import timezone

from .serializers import *

current_datetime = timezone.now()

# Check id exists in database 
def id_exists(table_name, id_to_check):
    query = f"SELECT 1 FROM {table_name} WHERE id = %s"
    
    with connection.cursor() as cursor:
        cursor.execute(query, [id_to_check])
        result = cursor.fetchone()
    
    return result is not None

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
        artist_id = self.kwargs.get('pk')  # Get the artist's primary key from the URL
        if id_exists('dashboard_artist', artist_id):
            if serializer.is_valid():
                artist_data = serializer.validated_data
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
        else:
            return Response({"message": "Artist not found"}, status=status.HTTP_404_NOT_FOUND)



# Artist Delete API        
class ArtistDeleteAPIView(generics.DestroyAPIView):

    def destroy(self, request, *args, **kwargs):
        artist_id = self.kwargs.get('pk')  # Get the artist's primary key from the URL
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE dashboard_artist "
                "SET deleted_at=%s "
                "WHERE id=%s",
                [current_datetime, artist_id]
            )
            # Check if the query was successful
            if cursor.rowcount > 0:
                # The query affected at least one row, meaning the artist was deleted
                return Response({"message": "Artist deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
            else:
                # The query did not affect any rows, meaning the artist was not found
                return Response({"message": "Artist not found"}, status=status.HTTP_404_NOT_FOUND)

# Artist Detail API
class ArtistDetailAPIView(generics.RetrieveAPIView):

    def get(self, request, *args, **kwargs):
        artist_id = self.kwargs.get('pk')  # Get the artist's primary key from the URL
        with connection.cursor() as cursor:
            # Fetch artist details
            cursor.execute(
                "SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE id = %s;",
                [artist_id]
            )
            artist_data = dictfetchall(cursor)

            if artist_data is None:
                return Response({"message": "Artist not found"}, status=404)

            # Fetch the list of songs by the artist
            cursor.execute(
                "SELECT id, title, album_name, genre, release_year FROM dashboard_song WHERE artist_id = %s;",
                [artist_id]
            )
            songs_data = dictfetchall(cursor)

        data = {
            "artist": artist_data,
            "songs": songs_data,
        }
        return Response(data)
    

# Song Create API
class SongCreateAPIView(generics.CreateAPIView):

    def create(self, request, *args, **kwargs):
        artist_id = self.kwargs.get('artist_id')  # Get the artist's ID from the URL
        song_data = request.data
        serializer = SongSerializer(data=song_data)
        album_name = song_data.get('album_name', '')
        release_year = song_data.get('release_year', 0) 

        if serializer.is_valid():
            with connection.cursor() as cursor:
                # Insert the song data using a raw SQL query
                cursor.execute(
                    "INSERT INTO dashboard_song (title, album_name, genre, release_year, artist_id, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;",
                    [
                        song_data['title'],
                        album_name,
                        song_data['genre'],
                        release_year,
                        artist_id,
                        current_datetime,
                        current_datetime,
                    ]
                )
                cursor.execute("SELECT LASTVAL();")
                new_song_id = cursor.fetchone()[0]
                cursor.execute("SELECT id, title, album_name, genre, release_year FROM dashboard_song WHERE id = %s AND deleted_at IS NULL", [new_song_id])
                song = dictfetchall(cursor)
            return Response({'song': song[0], 'message':'Song Created Successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Song Update API
class SongUpdateAPIView(generics.UpdateAPIView):

    def update(self, request, *args, **kwargs):

        data = request.data
        serializer = SongSerializer(data=data)
        song_id = self.kwargs.get('pk')
        if id_exists('dashboard_song', song_id):
            if serializer.is_valid():
                song_data = serializer.validated_data
                album_name = song_data.get('album_name', '')
                release_year = song_data.get('release_year', 0) 
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE dashboard_song "
                        "SET title=%s, album_name=%s, genre=%s, release_year=%s, updated_at=%s "
                        "WHERE id=%s",
                        [song_data['title'], album_name, song_data['genre'], release_year, current_datetime, song_id]
                    )
                return Response({"message": "Song updated successfully"}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Song not found"}, status=status.HTTP_404_NOT_FOUND)


def dictfetchall(cursor):
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]