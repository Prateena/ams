from django.urls import path
from dashboard import views

urlpatterns = [
    # accounts
    path('', views.login_view, name="login"),
    path('signup/', views.signup_view, name="signup"),
    path('logout/', views.logout_view, name="logout"),

    # dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # user crud
    path('create/user/', views.create_user, name="create-user"),
    path('users/', views.read_users, name="users"),
    path('update/user/<int:user_id>/', views.update_user, name='update-user'),
    path('delete/user/<int:user_id>/', views.delete_user, name="delete-user"),

    # artist crud
    path('create/artist/', views.create_artist, name="create-artist"),
    path('artists/', views.read_artists, name="artists"),
    path('update/artist/<int:artist_id>/', views.update_artist, name='update-artist'),
    path('delete/artist/<int:artist_id>/', views.delete_artist, name="delete-artist"),
    path('detail/artist/<int:artist_id>/', views.artist_detail, name='detail-artist'),

    # song crud
    path('artist/<int:artist_id>/create-song/', views.create_song, name="create-song"),
]