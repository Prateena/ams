from django.urls import path
from .views import *

urlpatterns = [
    path('artists/', ArtistList.as_view(), name='api-artist-list'),
    path('artists/create/', ArtistCreateAPIView.as_view(), name='api-create-artist'),
    path('artists/update/<int:pk>/', ArtistUpdateAPIView.as_view(), name='api-update-artist'),
    path('artists/delete/<int:pk>/', ArtistDeleteAPIView.as_view(), name='api-delete-artist'),
    path('artist/detail/<int:pk>/', ArtistDetailAPIView.as_view(), name='api-artist-detail'),
]