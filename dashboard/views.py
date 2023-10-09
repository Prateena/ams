from django.db import connection
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password

from .forms import ArtistForm, UserForm, UserUpdateForm


# Get the current datetime
current_datetime = timezone.now()


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
def read_users(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, first_name, last_name, email, phone, dob, gender, address FROM dashboard_customuser WHERE is_superuser=False")
        users = cursor.fetchall()
    return render(request, 'user/list.html', {'users': users})


# Update User
@login_required
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
def delete_user(request, user_id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM dashboard_customuser WHERE id=%s", [user_id])
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
        cursor.execute("SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year FROM dashboard_artist WHERE deleted_at IS NULL")
        artists = cursor.fetchall()
    return render(request, 'artist/list.html', {'artists': artists})


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