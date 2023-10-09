from django.urls import path
from dashboard import views

urlpatterns = [
    # accounts
    path('', views.login_view, name="login"),
    path('signup/', views.signup_view, name="signup"),
    path('logout/', views.logout_view, name="logout"),

    # dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # artist crud
    path('create/artist/', views.create_artist, name="create-artist"),
    path('artists/', views.read_artists, name="artists"),

]