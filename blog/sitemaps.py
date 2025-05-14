from django.contrib.sitemaps import Sitemap
from.models import Post, Category, Announcement  
from django.urls import reverse

class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Post.objects.all()

    def lastmod(self, obj):
        return obj.post_date

class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Category.objects.all()

class AnnouncementSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return Announcement.objects.all()

    def lastmod(self, obj):
        return obj.created_at

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return ['home', 'recommendations', 'get_started', 'posts', 'categories_list', 'handle_dropdown', 'search']  # Add other static view names

    def location(self, item):
        return reverse(item)