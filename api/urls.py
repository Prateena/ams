from django.urls import path
from .views import *

urlpatterns = [
    # user login and register 
    path('login/', LoginView.as_view()),
    path('register/', RegisterAPIView.as_view()),

    # user crud
    path('users/', UserList.as_view(), name='api-user-list'),
    path('user/create/', UserCreateAPIView.as_view(), name='api-create-user'), 
    path('user/update/<int:pk>/', UserUpdateAPIView.as_view(), name='api-update-user'),
    path('user/delete/<int:pk>/', UserDeleteAPIView.as_view(), name='api-delete-user'), 

    # artist crud
    path('artists/', ArtistList.as_view(), name='api-artist-list'),
    path('artist/create/', ArtistCreateAPIView.as_view(), name='api-create-artist'),
    path('artist/update/<int:pk>/', ArtistUpdateAPIView.as_view(), name='api-update-artist'),
    path('artist/delete/<int:pk>/', ArtistDeleteAPIView.as_view(), name='api-delete-artist'),
    path('artist/detail/<int:pk>/', ArtistDetailAPIView.as_view(), name='api-artist-detail'),

    # song create, update and delete
    path('song/create/<int:artist_id>/', SongCreateAPIView.as_view(), name='api-create-song'),
    path('song/update/<int:pk>/', SongUpdateAPIView.as_view(), name='api-update-song'),
    path('song/delete/<int:pk>/', SongDeleteAPIView.as_view(), name='api-delete-song'),

    # export artists and songs csv
    path('export-artists-songs-csv/', ExportArtistSongCSVAPIView.as_view(), name='export-artist-and-song-csv'),

    # import artists and songs csv
    path('import-artists-songs-csv/', ImportArtistSongCSVAPIView.as_view(), name='import-artist-and-song-csv'),


]