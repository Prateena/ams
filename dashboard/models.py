from django.db import models
from django.utils import timezone


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
    
    
class Artist(DateTimeModel, models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["id"]
        verbose_name = 'Artist'
        verbose_name_plural = 'Artists' 

    def __str__(self):
        return self.name
    
    
class Song(DateTimeModel, models.Model):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    release_year = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ["id"]
        verbose_name = 'Song'
        verbose_name_plural = 'Songs' 

    def __str__(self):
        return self.title