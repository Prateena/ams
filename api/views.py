import csv 
from io import TextIOWrapper

from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated

from django.db import connection
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password

from .serializers import *

current_datetime = timezone.now()

class AuthMixin:
    permission_classes = [IsAuthenticated]

# Check id exists in database 
def id_exists(table_name, id_to_check):
    query = f"SELECT 1 FROM {table_name} WHERE id = %s AND deleted_at IS NULL"
    
    with connection.cursor() as cursor:
        cursor.execute(query, [id_to_check])
        result = cursor.fetchone()
    
    return result is not None

# User Login API
class LoginView(ObtainAuthToken):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})

        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
                'token': token.key,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email':user.email,      
        }, 200)
    
# User Register API  
class RegisterAPIView(ObtainAuthToken):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO dashboard_customuser (username, first_name, last_name, email, password, phone, dob, gender, address, is_superuser, is_staff, is_active, date_joined) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [data['email'], data['first_name'], data['last_name'], data['email'], make_password(data['password']), data['phone'], data['dob'], data['gender'], data['address'], False, False, True, current_datetime]
                )
                cursor.execute("SELECT LASTVAL();")
                user_id = cursor.fetchone()[0]
                cursor.execute("SELECT id, phone, dob, gender, address FROM dashboard_customuser WHERE id = %s", [user_id])
                user = cursor.fetchall()[0]

                cursor.execute(
                    "INSERT INTO auth_user (username, first_name, last_name, email, password, is_superuser, is_staff, is_active, date_joined) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [data['email'], data['first_name'], data['last_name'], data['email'], make_password(data['password']), False, False, True, current_datetime]
                )
                cursor.execute("SELECT LASTVAL();")
                auth_user_id = cursor.fetchone()[0]
                cursor.execute("SELECT id, username, first_name, last_name, email, password, is_superuser, is_staff, is_active, date_joined FROM auth_user WHERE id = %s", [auth_user_id])
                auth_user = cursor.fetchall()[0]

            token, _ = Token.objects.get_or_create(user_id=auth_user[0])

            return Response({
                'token': token.key,
                'id': user[0],
                'username': auth_user[1],
                'email': auth_user[4],
                'first_name': auth_user[2],
                'last_name': auth_user[3],
                'phone': user[1],
                'dob': user[2],
                'gender': user[3],
                'address': user[4],
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Artist List API
class ArtistList(AuthMixin, APIView):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE deleted_at IS NULL ORDER BY id")
            artists = dictfetchall(cursor)
        return Response(artists)

# Artist Create API
class ArtistCreateAPIView(AuthMixin, generics.CreateAPIView):
    
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
class ArtistUpdateAPIView(AuthMixin, generics.UpdateAPIView):

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
                        [artist_data['name'], data['gender'], artist_data['dob'], artist_data['address'], artist_data['no_of_albums_released'], artist_data['first_release_year'], current_datetime, artist_id]
                    )
                return Response({"message": "Artist updated successfully"}, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Artist not found"}, status=status.HTTP_404_NOT_FOUND)



# Artist Delete API        
class ArtistDeleteAPIView(AuthMixin, generics.DestroyAPIView):

    def destroy(self, request, *args, **kwargs):
        artist_id = self.kwargs.get('pk')  # Get the artist's primary key from the URL
        if id_exists('dashboard_artist', artist_id):
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE dashboard_artist "
                    "SET deleted_at=%s "
                    "WHERE id=%s",
                    [current_datetime, artist_id]
                )
            return Response({"message": "Artist deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "Artist not found"}, status=status.HTTP_404_NOT_FOUND)

# Artist Detail API
class ArtistDetailAPIView(AuthMixin, generics.RetrieveAPIView):

    def get(self, request, *args, **kwargs):
        artist_id = self.kwargs.get('pk')  # Get the artist's primary key from the URL
        if id_exists('dashboard_artist', artist_id):

            with connection.cursor() as cursor:
                # Fetch artist details
                cursor.execute(
                    "SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE id = %s AND deleted_at IS NULL;",
                    [artist_id]
                )
                artist_data = dictfetchall(cursor)

                if artist_data is None:
                    return Response({"message": "Artist not found"}, status=404)

                # Fetch the list of songs by the artist
                cursor.execute(
                    "SELECT id, title, album_name, genre, release_year FROM dashboard_song WHERE artist_id = %s AND deleted_at IS NULL;",
                    [artist_id]
                )
                songs_data = dictfetchall(cursor)

            data = {
                "artist": artist_data,
                "songs": songs_data,
            }
            return Response(data)
        else:
            return Response({"message": "Artist not found"}, status=status.HTTP_404_NOT_FOUND)
    

# Song Create API
class SongCreateAPIView(AuthMixin, generics.CreateAPIView):

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
class SongUpdateAPIView(AuthMixin, generics.UpdateAPIView):

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

# Song Delete API        
class SongDeleteAPIView(AuthMixin, generics.DestroyAPIView):

    def destroy(self, request, *args, **kwargs):
        song_id = self.kwargs.get('pk')  # Get the artist's primary key from the URL
        if id_exists('dashboard_song', song_id):
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE dashboard_song "
                    "SET deleted_at=%s "
                    "WHERE id=%s",
                    [current_datetime, song_id]
                )
            return Response({"message": "Song deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "Song not found"}, status=status.HTTP_404_NOT_FOUND)

# Export Artist and Song API 
class ExportArtistSongCSVAPIView(AuthMixin, APIView):

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="artist_and_their_songs.csv"'

        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, dob, gender, first_release_year, no_of_albums_released, address FROM dashboard_artist ORDER BY id")
            artists = cursor.fetchall()

            cursor.execute("SELECT id, title, artist_id, album_name, genre, release_year  FROM dashboard_song ORDER BY id")
            songs = cursor.fetchall()

        writer = csv.writer(response)
        writer.writerow(['Artist ID', 'Artist Name', 'Birthdate', 'Gender', 'First Release Year', 'No of Albums Released', 'Address'])

        for artist in artists:
            writer.writerow(artist)

        # Write header for song data
        song_header = ['Song ID', 'Song Title', 'Artist ID', 'Album Name', 'Genre', 'Release Year']
        writer.writerow(song_header)

        # Write song data
        for song in songs:
            writer.writerow(song)
        return response
    
def artist_exists(artist_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM dashboard_artist WHERE id = %s", [artist_id])
        row = cursor.fetchone()
    return row is not None

def song_exists(song_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM dashboard_song WHERE id = %s", [song_id])
        row = cursor.fetchone()
    return row is not None

# Import Artist and Song API 
class ImportArtistSongCSVAPIView(AuthMixin, APIView):
    serializer_class = CSVImportSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            csv_file = request.data['csv_file']
            with connection.cursor() as cursor:
                csv_file_wrapper = TextIOWrapper(csv_file.file, encoding='utf-8')
                csv_reader = csv.reader(csv_file_wrapper)

                # Initialize header flags
                artist_header = False
                song_header = False

                for row in csv_reader:
                    if not artist_header and row == ['Artist ID', 'Artist Name', 'Birthdate', 'Gender', 'First Release Year', 'No of Albums Released', 'Address']:
                        # Skip the artist header
                        artist_header = True
                        continue

                    if not song_header and row == ['Song ID', 'Song Title', 'Artist ID', 'Album Name', 'Genre', 'Release Year']:
                        # Skip the song header
                        song_header = True
                        continue

                    if artist_header and len(row) == 7:
                        # Process artist data
                        artist_id = int(row[0])
                        if not artist_exists(artist_id):
                            cursor.execute(
                                    "INSERT INTO dashboard_artist (id, name, dob, gender, first_release_year, no_of_albums_released, address, created_at, updated_at) "
                                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                    [row[0], row[1], row[2], row[3], row[4], row[5], row[6], current_datetime, current_datetime]
                                    )

                    if song_header and len(row) == 6:
                        # Process song data
                        song_id = int(row[0])
                        if not song_exists(song_id):
                            cursor.execute(
                                    "INSERT INTO dashboard_song (id, title, artist_id, album_name, genre, release_year, created_at, updated_at) "
                                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                    [row[0], row[1], row[2], row[3], row[4], row[5], current_datetime, current_datetime]
                                )

            return Response({'message':'CSV Imported Successfully'}, status=status.HTTP_200_OK) 
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

def dictfetchall(cursor):
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]