from django.db import connection
from django.utils import timezone
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password

from .forms import ArtistForm


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


        # Execute a raw SQL query to insert the user into the database
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

        return redirect('login')  # Redirect to the login page after signup
    else:
        return render(request, 'user/signup.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['email']
        password = request.POST['password']

        # Execute a raw SQL query to retrieve the user's data
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password FROM auth_user WHERE username = %s",
                [username]
            )
            user_data = cursor.fetchone()

        if user_data:
            user_id, username, hashed_password = user_data
            # Verify the password
            passwords_match = check_password(password, hashed_password)
            if passwords_match:
                user = User.objects.get(id=user_id)
                login(request, user)  # Log in the user
                return redirect('dashboard')

        # Handle invalid login
        return render(request, 'user/login.html', {'error_message': 'Invalid login credentials'})

    else:
        return render(request, 'user/login.html')


def logout_view(request):
    if request.user.is_authenticated:
        # Execute a raw SQL query to clear the user's session
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auth_user SET last_login = NULL WHERE id = %s",
                [request.user.id]
            )

        # Log the user out by calling Django's logout function
        request.session.flush()

    return redirect('login')


@login_required
def dashboard_view(request):
    return render(request, 'layouts/dashboard.html')


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
        cursor.execute("SELECT id, name, gender, dob, address, no_of_albums_released, first_release_year address FROM dashboard_artist")
        artists = cursor.fetchall()
    return render(request, 'artist/list.html', {'artists': artists})


