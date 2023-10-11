import csv
from io import TextIOWrapper

from django.db import connection
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.urls import reverse

from .forms import *
from .models import *


# Get the current datetime
current_datetime = timezone.now()


def superuser_required(view_func):
    """
    Custom decorator to allow access to only superusers.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden("You do not have permission to perform this action.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def login_authentication(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')  # Redirect to the dashboard page
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def signup_view(request):
    if request.method == 'POST':
        username = request.POST['email']
        password = make_password(request.POST['password'])
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        phone = request.POST['phone']
        dob = request.POST['dob']
        gender = request.POST['gender']
        address = request.POST['address']


        # Executing a raw SQL query to insert the user into the database
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO dashboard_customuser (username, password, first_name, last_name, email, is_superuser, is_staff, is_active, date_joined, phone, dob, gender, address) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [username, password, first_name, last_name,
                    email, False, False, True, current_datetime, phone, dob, gender, address]
            )
            cursor.execute(
                "INSERT INTO auth_user (username, password, first_name, last_name, email, is_superuser, is_staff, is_active, date_joined) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [username, password, first_name, last_name,
                    email, False, False, True, current_datetime]
            )

        return redirect('login')  # Redirecting to the login page after signup
    else:
        return render(request, 'accounts/signup.html')


@login_authentication
def login_view(request):
    if request.method == 'POST':
        username = request.POST['email']
        password = request.POST['password']

        # Executing a raw SQL query to retrieve the user's data
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password FROM auth_user WHERE username = %s",
                [username]
            )
            user_data = cursor.fetchone()

        if user_data:
            user_id, username, hashed_password = user_data
            # Verifying the password
            passwords_match = check_password(password, hashed_password)
            if passwords_match:
                user = User.objects.get(id=user_id)
                login(request, user)  # Logging in the user
                return redirect('dashboard')

        # Handling invalid login
        return render(request, 'accounts/login.html', {'error_message': 'Invalid login credentials'})

    else:
        return render(request, 'accounts/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        # Executing a raw SQL query to clear the user's session
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auth_user SET last_login = NULL WHERE id = %s",
                [request.user.id]
            )

        # Logging the user out by calling Django's logout function
        request.session.flush()

    return redirect('login')


@login_required
def dashboard_view(request):
    return render(request, 'layouts/dashboard.html')


# Create User
@login_required
@superuser_required
def create_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO dashboard_customuser (username, first_name, last_name, email, password, phone, dob, gender, address, is_superuser, is_staff, is_active, date_joined) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [data['email'], data['first_name'], data['last_name'], data['email'], make_password(data['password']), data['phone'], data['dob'], data['gender'], data['address'], False, False, True, current_datetime]
                )
                cursor.execute(
                    "INSERT INTO auth_user (username, first_name, last_name, email, password, is_superuser, is_staff, is_active, date_joined) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [data['email'], data['first_name'], data['last_name'], data['email'], make_password(data['password']), False, False, True, current_datetime]
                )
            return redirect('users')
    else:
        form = UserForm()
    return render(request, 'user/form.html', {'form': form})


# Read User
@login_required
@superuser_required
def read_users(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, first_name, last_name, email, phone, dob, gender, address FROM dashboard_customuser WHERE is_superuser=False ORDER BY id")
        users = cursor.fetchall()
    return render(request, 'user/list.html', {'users': users})


# Update User
@login_required
@superuser_required
def update_user(request, user_id):
    user = None
    if request.method == 'POST':
        form = UserUpdateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute("SELECT email FROM dashboard_customuser WHERE id=%s", [user_id])
                auth_user_email = cursor.fetchone()

                cursor.execute(
                    "UPDATE auth_user "
                    "SET username=%s, first_name=%s, last_name=%s, email=%s"
                    "WHERE email=%s",
                    [data['email'], data['first_name'], data['last_name'], data['email'], auth_user_email]
                )
                cursor.execute(
                    "UPDATE dashboard_customuser "
                    "SET username=%s, first_name=%s, last_name=%s, email=%s, phone=%s, dob=%s, gender=%s, address=%s "
                    "WHERE id=%s",
                    [data['email'], data['first_name'], data['last_name'], data['email'], data['phone'], data['dob'], data['gender'], data['address'], user_id]
                )
   
            return redirect('users')
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT first_name, last_name, email, phone, dob, gender, address FROM dashboard_customuser WHERE id=%s", [user_id])
            user = cursor.fetchone()
        if user:
            form = UserUpdateForm(initial={
                'first_name': user[0],
                'last_name': user[1],
                'email': user[2],
                'phone': user[3],
                'dob': user[4],
                'gender': user[5],
                'address': user[6],
            })
        else:
            return redirect('users')
    return render(request, 'user/form.html', {'form': form})


# Delete User
@login_required
@superuser_required
def delete_user(request, user_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT email FROM dashboard_customuser WHERE id=%s", [user_id])
        auth_user_email = cursor.fetchone()
        cursor.execute("DELETE FROM dashboard_customuser WHERE id=%s", [user_id])
        cursor.execute("DELETE FROM auth_user WHERE email=%s", auth_user_email)
    return redirect('users')


# Create Artist
@login_required
def create_artist(request):
    if request.method == 'POST':
        form = ArtistForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO dashboard_artist (name, gender, dob, address, no_of_albums_released, first_release_year, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    [data['name'], data['gender'], data['dob'], data['address'], data['no_of_albums_released'], data['first_release_year'], current_datetime, current_datetime]
                )
            return redirect('artists')
    else:
        form = ArtistForm()
    return render(request, 'artist/form.html', {'form': form})


# Read Artist
@login_required
def read_artists(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE deleted_at IS NULL ORDER BY id")
        artists = cursor.fetchall()
    return render(request, 'artist/list.html', {'artists': artists, 'form':CSVImportForm()})


# Update Artist
@login_required
def update_artist(request, artist_id):
    artist = None
    if request.method == 'POST':
        form = ArtistForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE dashboard_artist "
                    "SET name=%s, gender=%s, dob=%s, address=%s, no_of_albums_released=%s, first_release_year=%s, updated_at=%s "
                    "WHERE id=%s",
                    [data['name'], data['gender'], data['dob'], data['address'], data['no_of_albums_released'], data['first_release_year'], current_datetime, artist_id]
                )
            return redirect('artists')
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE id=%s", [artist_id])
            artist = cursor.fetchone()
        if artist:
            form = ArtistForm(initial={
                'name': artist[0],
                'gender': artist[1],
                'dob': artist[2],
                'address': artist[3],
                'no_of_albums_released': artist[4],
                'first_release_year': artist[5],
            })
        else:
            return redirect('artists')
    return render(request, 'artist/form.html', {'form': form})


# Delete Artist
@login_required
@superuser_required
def delete_artist(request, artist_id):
    # Get the current timestamp
    deleted_at = timezone.now()

    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE dashboard_artist "
            "SET deleted_at=%s "
            "WHERE id=%s",
            [deleted_at, artist_id]
        )

    return redirect('artists')


# Read Songs of Particular Artist
def read_songs(artist_id):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT artist_id, id, title, album_name, genre, release_year FROM dashboard_song WHERE artist_id = %s ORDER BY id",
            [artist_id]
        )
        songs = cursor.fetchall()
    return songs


# Artist Detail
@login_required
def artist_detail(request, artist_id):
    artist = get_object_or_404(Artist, pk=artist_id)
    songs = read_songs(artist_id)  # Retrieve songs for the artist
    form = SongForm()
    return render(request, 'artist/detail.html', {'artist': artist, 'songs': songs, 'form': form})


# Create Song of a Particular Artist
@login_required
def create_song(request, artist_id):
    if request.method == 'POST':
        form = SongForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO dashboard_song (artist_id, title, album_name, genre, release_year, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    [artist_id, data['title'], data['album_name'], data['genre'], data['release_year'], current_datetime, current_datetime]
                )
            return redirect('detail-artist', artist_id=artist_id)
    else:
        form = SongForm()
    return render(request, 'song/form.html', {'form': form})


# Update Song
@login_required
def update_song(request, artist_id, song_id):
    if request.method == 'POST':
        form = SongForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE dashboard_song "
                    "SET title = %s, album_name=%s, genre=%s, release_year=%s, updated_at=%s "
                    "WHERE id = %s",
                    [data['title'], data['album_name'], data['genre'], data['release_year'], current_datetime, song_id]
                )
                cursor.execute("SELECT id, name FROM dashboard_artist WHERE id=%s",[artist_id])
                artist = cursor.fetchone()

            return redirect('detail-artist', artist_id=artist_id)
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT title, album_name, genre, release_year FROM dashboard_song WHERE id=%s", [song_id])
            song = cursor.fetchone()
            cursor.execute("SELECT id, name FROM dashboard_artist WHERE id=%s",[artist_id])
            artist = cursor.fetchone()
        if song:
            form = SongForm(initial={
                'title': song[0],
                'album_name': song[1],
                'genre': song[2],
                'release_year': song[3],
            })
        else:
            return redirect('detail-artist', artist_id=artist_id)
    return render(request, 'song/form.html', {'form': form, 'artist':artist})


# Delete Song
@login_required
def delete_song(request, artist_id, song_id):
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM dashboard_song WHERE id = %s",
            [song_id]
        )

    return redirect('detail-artist', artist_id=artist_id)


# Export Artists CSV
def export_artist_and_song_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="artist_and_their_songs.csv"'

    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, dob, gender, first_release_year, no_of_albums_released, address FROM dashboard_artist")
        artists = cursor.fetchall()

        cursor.execute("SELECT id, title, artist_id, album_name, genre, release_year  FROM dashboard_song")
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


def import_artist_and_song_csv(request):
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']

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

                    print(len(row))

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
                            cursor.execute("""
                                    INSERT INTO dashboard_song (id, title, artist_id, album_name, genre, release_year)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, row)

            return HttpResponse('CSV file successfully imported.')
    else:
        form = CSVImportForm()

    return render(request, 'artist/detail.html', {'form': form})