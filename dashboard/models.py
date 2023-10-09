from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager


class DateTimeModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        auto_now=False,
    )
    updated_at = models.DateTimeField(
        auto_now_add=False,
        auto_now=True,
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self):
        self.deleted_at = timezone.now()
        super().save()


GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    phone = models.CharField(max_length=15)
    dob = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.CharField(max_length=255)
    groups = models.ManyToManyField(Group, blank=True, related_name='custom_user_groups')
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='custom_user_permissions'
    )
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ["id"]
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users' 

    def __str__(self):
        return self.username
    
    
class Artist(DateTimeModel, models.Model):
    name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    first_release_year = models.PositiveIntegerField()
    no_of_albums_released = models.PositiveIntegerField()
    address = models.CharField(max_length=255)
    
    class Meta:
        ordering = ["id"]
        verbose_name = 'Artist'
        verbose_name_plural = 'Artists' 

    def __str__(self):
        return self.name
    

GENRE_CHOICES = (
    ('rnb', 'rnb'),
    ('country', 'country'),
    ('classic','classic'),
    ('rock','rock'),
    ('jazz','jazz'),
)


class Song(DateTimeModel, models.Model):
    title = models.CharField(max_length=100)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    album_name = models.CharField(max_length=100)
    genre = models.CharField(max_length=10, choices=GENRE_CHOICES)
    release_year = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ["id"]
        verbose_name = 'Song'
        verbose_name_plural = 'Songs' 

    def __str__(self):
        return self.title