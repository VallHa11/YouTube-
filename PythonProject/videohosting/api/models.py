from django.contrib.auth.models import AbstractUser
from django.db import models



class User(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.username

class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Комментарий от {self.author.username} к видео {self.video.title}"

class Reaction(models.Model):
    LIKE = "like"
    DISLIKE = "dislike"
    TYPES = [
        (LIKE, "👍 Like"),
        (DISLIKE, "👎 Dislike"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="reactions")
    type = models.CharField(max_length=7, choices=TYPES)

    class Meta:
        unique_together = ("user", "video")  # Один пользователь — одна реакция

    def __str__(self):
        return f"{self.user.username}: {self.type} → {self.video.title}"

class Subscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscribed_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')

    class Meta:
        unique_together = ("subscriber", "subscribed_to")

    def __str__(self):
        return f"{self.subscriber.username} → {self.subscribed_to.username}"

from django.db import models

class VideoUpload(models.Model):
    upload_id = models.CharField(max_length=100, unique=True)
    file_name = models.CharField(max_length=255)
    total_chunks = models.IntegerField()
    uploaded_chunks = models.IntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

