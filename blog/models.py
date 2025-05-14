from django.db import models
from django.conf import settings  
from django.urls import reverse
from datetime import datetime, date
#from ckeditor.fields import RichTextField
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth import get_user_model
from PIL import Image as PILImage
import io
from django.core.files.base import ContentFile
from cloudinary.models import CloudinaryField 
from django.contrib.contenttypes.fields import GenericForeignKey

# Get the user model based on AUTH_USER_MODEL
User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("home")
# models.py

class Profile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    bio = models.TextField()
    profile_pic = CloudinaryField('image', null=True, blank=True, folder="images/profile")  
    website_url = models.CharField(max_length=255, null=True, blank=True)
    linkedin_url = models.CharField(max_length=255, null=True, blank=True)
    facebook_url = models.CharField(max_length=255, null=True, blank=True)
    twitter_url = models.CharField(max_length=255, null=True, blank=True)
    instagram_url = models.CharField(max_length=255, null=True, blank=True)
    pinterest_url = models.CharField(max_length=255, null=True, blank=True)
   
    
    

    def __str__(self):
        return str(self.user)
    
    def get_absolute_url(self):
        return reverse("home")
    
    def followers_count(self):
        return self.user.followers.count()

    def following_count(self):
        return self.user.following.count()

    def is_following(self, user):
        return Follow.objects.filter(follower=user, followed=self.user).exists()

    def is_followed_by(self, user):
        return Follow.objects.filter(follower=self.user, followed=user).exists()
    
    
    
class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')  # Prevent duplicate follows
        
    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"
class Post(models.Model):
    title = models.CharField(max_length=255)
    header_image = CloudinaryField('image', null=True, blank=True, folder="images/postimages")
    title_tag = models.CharField(max_length=255, default="My Blog")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Update to use AUTH_USER_MODEL
    # body = models.TextField()
    body = CKEditor5Field('Text', config_name='extends')
    category = models.CharField(max_length=255, default="Computer Science", null=True)
    snippet = models.CharField(max_length=255)
    likes = models.ManyToManyField(User, related_name="blog_posts")

    post_date = models.DateField(auto_now_add=True)

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.title + " " + str(self.author)

    def get_absolute_url(self):
        return reverse("home")
        # return reverse("article_detail", args=(str(self.pk),))
class Comments(models.Model):
    comment = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    body = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.comment.title} - {self.name}'
    
    class Meta:
        ordering = ['-date_added']  # Newest comments first



class Announcement(models.Model):
    TITLE_CHOICES = [
        ('bootcamp', 'Bootcamp'),
        ('internship', 'Internship Opportunity'),
        ('webinar', 'Webinar'),
        ('career', 'Career Opportunity'),
        ('scholarship', 'Scholarship'),
        ('other', 'Other'),
      
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    type = models.CharField(max_length=50, choices=TITLE_CHOICES)
    image = models.ImageField(upload_to='announcements/', blank=True, null=True)
    announcement_date = models.DateField()
    location = models.CharField(max_length=200, blank=True, null=True)  # Physical or online
    registration_link = models.URLField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)  # Especially for webinars
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse("announcements")
    


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('comment', 'Comment'),
    )

    recipient = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    actor = models.ForeignKey(User, related_name='actions', on_delete=models.CASCADE)
    verb = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    target_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.actor} {self.verb} {self.target} for {self.recipient}"

    class Meta:
        ordering = ['-timestamp']

    @classmethod
    def cleanup_old_notifications(cls, user, days=1):
        """Remove notifications older than specified days that have been read"""
        from django.utils import timezone
        import datetime
        
        cutoff_date = timezone.now() - datetime.timedelta(days=days)
        cls.objects.filter(
            recipient=user,
            is_read=True,
            timestamp__lt=cutoff_date
        ).delete()
        
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

def send_notification_to_user(recipient, notification_data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{recipient.id}',
        {
            'type': 'send_notification',
            'notification': notification_data
        }
    )
    
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Notification)
def send_notification(sender, instance, created, **kwargs):
    if created:
        notification_data = {
            'id': instance.id,
            'actor': instance.actor.username,
            'verb': instance.verb,
            'target': str(instance.target) if instance.target else '',
            'timestamp': instance.timestamp.isoformat(),
            'is_read': instance.is_read,
        }
        send_notification_to_user(instance.recipient, notification_data)

class UserInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='interactions')
    viewed_at = models.DateTimeField(auto_now_add=True)
    view_duration = models.IntegerField(default=0)  # in seconds
    
    class Meta:
        unique_together = ('user', 'post')
