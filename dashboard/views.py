import csv
from io import TextIOWrapper

from django.urls import reverse
from django.db import connection
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import *
from .models import *


# Get the current datetime
current_datetime = timezone.now()

# Check id exists in database 
def id_exists(table_name, id_to_check):
    query = f"SELECT 1 FROM {table_name} WHERE id = %s"
    
    with connection.cursor() as cursor:
        cursor.execute(query, [id_to_check])
        result = cursor.fetchone()
    
    return result is not None

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


def paginate(query, request, items_per_page=10):
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    
    paginator = Paginator(results, items_per_page)
    page_number = request.GET.get('page')
    
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)  # Display the first page
        page_number = 1  # Set the page number to 1
    except EmptyPage:
        page = paginator.page(paginator.num_pages)  # Display the last page
        page_number = paginator.num_pages  # Set the page number to the last page
    
    return page.object_list, page


def signup_view(request):
    if request.method == 'POST':

        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            username = data['email']
            password = make_password(data['password'])
            first_name = data['first_name']
            last_name = data['last_name']
            email = data['email']
            phone = data['phone']
            dob = data['dob']
            gender = data['gender']
            address = data['address']

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
        form = UserForm()
    return render(request, 'accounts/signup.html', {'form': form, 'message':'Account Created Successfully! Please Login using your credentials'})


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
                user = User(id=user_id, username=username, password=hashed_password)
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
    query = "SELECT id, first_name, last_name, email, phone, dob, gender, address FROM dashboard_customuser WHERE is_superuser=False ORDER BY id"
    
    # Define the number of items per page
    items_per_page = 10
    
    object_list, page = paginate(query, request, items_per_page)
    return render(request, 'user/list.html', {'users':object_list,'page':page})


# Update User
@login_required
@superuser_required
def update_user(request, user_id):
    user = None
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, email FROM dashboard_customuser WHERE id=%s", [user_id])
        custom_user = cursor.fetchone()
    if request.method == 'POST':
        form = UserUpdateForm(custom_user, request.POST)
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
            form = UserUpdateForm(custom_user, initial={
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
    if id_exists('dashboard_customuser',user_id):
        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM dashboard_customuser WHERE id=%s", [user_id])
            auth_user_email = cursor.fetchone()
            cursor.execute("DELETE FROM dashboard_customuser WHERE id=%s", [user_id])
            cursor.execute("DELETE FROM auth_user WHERE email=%s", auth_user_email)
        return redirect('users')
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT first_name, last_name, email, phone, dob, gender, address FROM dashboard_customuser")
            users = cursor.fetchall()
        return render(request, 'user/list.html', {'message': "User not found", 'users': users})


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
    query = "SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE deleted_at IS NULL ORDER BY id"
    # Define the number of items per page
    items_per_page = 10
    
    object_list, page_number = paginate(query, request, items_per_page)
    return render(request, 'artist/list.html', {'artists': object_list, 'form':CSVImportForm(), 'page':page_number})


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
            "SELECT artist_id, id, title, album_name, genre, release_year FROM dashboard_song WHERE artist_id = %s AND deleted_at IS NULL ORDER BY id",
            [artist_id]
        )
        songs = cursor.fetchall()
    return songs


# Artist Detail
@login_required
def artist_detail(request, artist_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE id=%s AND deleted_at IS NULL", [artist_id])
        artist = cursor.fetchone()
    songs = read_songs(artist_id)  # Retrieve songs for the artist
    form = SongForm()
    items_per_page = 10
    paginator = Paginator(songs, items_per_page)
    page_number = request.GET.get('page')

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)  # Display the first page
        page_number = 1  # Set the page number to 1
    except EmptyPage:
        page = paginator.page(paginator.num_pages)  # Display the last page
        page_number = paginator.num_pages  # Set the page number to the last page
    return render(request, 'artist/detail.html', {'artist': artist, 'songs': page.object_list, 'form': form, 'page': page})


# Create Song of a Particular Artist
@login_required
def create_song(request, artist_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE id=%s", [artist_id])
        artist = cursor.fetchone()
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
    return render(request, 'song/form.html', {'form': form, 'artist':artist})


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
    deleted_at = timezone.now()

    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE dashboard_song "
            "SET deleted_at=%s "
            "WHERE id=%s",
            [deleted_at, song_id]
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
            if not csv_file.name.endswith('.csv'):
                return JsonResponse({'error': 'Please upload a CSV file with the .csv extension.'}, status=400)

            with connection.cursor() as cursor:
                csv_file_wrapper = TextIOWrapper(csv_file.file, encoding='utf-8')
                csv_reader = csv.reader(csv_file_wrapper)

                # Initialize header flags
                artist_header = False
                song_header = False

                header_1 = ['Artist ID', 'Artist Name', 'Birthdate', 'Gender', 'First Release Year', 'No of Albums Released', 'Address']
                header_2 = ['Song ID', 'Song Title', 'Artist ID', 'Album Name', 'Genre', 'Release Year']
                valid_headers = False

                first_row = next(csv_reader)

                if first_row == header_1 or first_row == header_2:
                    valid_headers = True

                for row in csv_reader:
                    if valid_headers:
                        if not artist_header and first_row == header_1:
                            # Skip the artist header
                            artist_header = True
                            continue

                        if not song_header and row == header_2:
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
                                cursor.execute("""
                                        INSERT INTO dashboard_song (title, artist_id, album_name, genre, release_year, created_at, updated_at)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    """, [row[1], row[2], row[3], row[4], row[5], current_datetime, current_datetime]
                                    )
                    else:
                        return JsonResponse({'error': 'Invalid CSV format. Missing required headers.'}, status=400)
                cursor.execute("SELECT setval('dashboard_artist_id_seq', (SELECT id FROM dashboard_artist ORDER BY id DESC LIMIT 1))")
                cursor.execute("SELECT setval('dashboard_song_id_seq', (SELECT id FROM dashboard_song ORDER BY id DESC LIMIT 1))")
            return redirect('artists') 
    else:
        form = CSVImportForm()

    return render(request, 'artist/detail.html', {'form': form})