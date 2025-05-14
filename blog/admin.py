from django.contrib import admin
from .models import Announcement, Post,Category,Profile,Comments
admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Profile)
admin.site.register(Comments)
# Register your models here.
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'announcement_date', 'location', 'created_at')
    search_fields = ('title', 'content', 'type', 'location', 'registration_link')
    list_filter = ('type', 'announcement_date', 'location')
admin.site.register(Announcement, AnnouncementAdmin)
