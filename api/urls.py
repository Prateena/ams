from django.urls import path
from .views import *

urlpatterns = [
    # artist crud
    path('artists/', ArtistList.as_view(), name='api-artist-list'),
    path('artist/create/', ArtistCreateAPIView.as_view(), name='api-create-artist'),
    path('artist/update/<int:pk>/', ArtistUpdateAPIView.as_view(), name='api-update-artist'),
    path('artist/delete/<int:pk>/', ArtistDeleteAPIView.as_view(), name='api-delete-artist'),
    path('artist/detail/<int:pk>/', ArtistDetailAPIView.as_view(), name='api-artist-detail'),

    # song create
    path('song/create/<int:artist_id>/', SongCreateAPIView.as_view(), name='api-create-song'),
    path('song/update/<int:pk>/', SongUpdateAPIView.as_view(), name='api-update-song'),

]