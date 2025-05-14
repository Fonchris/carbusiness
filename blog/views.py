from datetime import timezone
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import CommentForm, PostForm, EditForm
from blog.models import Post, Category, Comments,Announcement
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.contrib import messages
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.decorators import login_required
from .models import  Follow, Notification, UserInteraction
from django.contrib.contenttypes.models import ContentType
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.mixins import LoginRequiredMixin
import json
# Create your views here.
class HomeView(ListView):
    model = Post
    template_name = 'index.html'
    ordering = ["-post_date"]

    def get_context_data(self, *args, **kwargs):
        category_menu = Category.objects.all()
        context = super(HomeView, self).get_context_data(*args, **kwargs)
        context["category_menu"] = category_menu
        return context
    
def CategoryListView(request):
    category_menu_list = Category.objects.all()
    return render(request, "categories_list.html", {'category_menu_list': category_menu_list})


def CategoryView(request, cats):
    category_posts = Post.objects.filter(category=cats)
    return render(request, "categories.html", {'cats': cats, 'category_posts': category_posts})





@login_required
def LikeView(request, pk):
    post = get_object_or_404(Post, id=request.POST.get("post_id"))
    liked = False

    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
        # Create notification if the liker is not the post author
        if post.author != request.user:
            notification = Notification.objects.create(
                recipient=post.author,
                actor=request.user,
                verb='like',
                target_content_type=ContentType.objects.get_for_model(Post),
                target_object_id=post.id,
            )
            # Send WebSocket notification
            channel_layer = get_channel_layer()
            notification_data = {
                'id': notification.id,
                'actor': notification.actor.username,
                'verb': notification.verb,
                'target': str(notification.target) if notification.target else '',
                'timestamp': notification.timestamp.isoformat(),
                'is_read': notification.is_read,
            }
            async_to_sync(channel_layer.group_send)(
                f'notifications_{post.author.id}',
                {
                    'type': 'send_notification',
                    'notification': notification_data
                }
            )

    return HttpResponseRedirect(reverse("article-detail", args=[str(pk)]))

class ArticleDetailView(DetailView):
    model = Post
    template_name = 'article_details.html'

    def get_context_data(self, *args, **kwargs):
        category_menu = Category.objects.all()
        context = super(ArticleDetailView, self).get_context_data(*args, **kwargs)
        post_object = get_object_or_404(Post,id=self.kwargs['pk'])
        total_likes= post_object.total_likes()
        liked= False
        if post_object.likes.filter(id=self.request.user.id).exists():
            liked=True
        context["total_likes"] = total_likes
        context["category_menu"] = category_menu
        context["liked"]= liked 
        return context
 
   
    
    
    
def process_image(image_file):
    try:
        image = Image.open(image_file)
        image.thumbnail((800, 600))  # Adjust dimensions as needed
        image = image.convert("RGB")
        webp_buffer = BytesIO()
        image.save(webp_buffer, format="WebP", quality=80)
        webp_file = InMemoryUploadedFile(webp_buffer, None, image_file.name.split('.')[0] + '.webp', 'image/webp', webp_buffer.getbuffer().nbytes, None)
        return webp_file
    except Exception as e:
        print(f"Error processing image: {e}")
        return image_file

class AddPostView(CreateView):
    model = Post
    form_class = PostForm
    template_name = 'add_blog_post.html'
    

    def form_valid(self, form):
        form.instance.author = self.request.user

        if 'header_image' in self.request.FILES:
            # Get the original uploaded file
            original_image = self.request.FILES['header_image']

            # Process the image (resize, convert)
            processed_image = process_image(original_image)

            # Assign the *processed* image to the form's instance
            form.instance.header_image = processed_image

        return super().form_valid(form)  # This now works correctly

    def get_success_url(self):
        return reverse_lazy('home')
    model = Post
    form_class = PostForm
    template_name = 'add_blog_post.html'
    # fields= '__all__'
    #added this function to permit me know which user is adding a blog post rather
    # than using the script which can be used by hackers, to also handle images
    def form_valid(self, form):
        form.instance.author = self.request.user
        if 'header_image' in self.request.FILES:
            form.instance.header_image = process_image(self.request.FILES['header_image'])
        super().form_valid(form)  # This saves the form
        return HttpResponseRedirect(self.get_success_url()) # Explicit redirect!

    def get_success_url(self): 
        return reverse_lazy('article-detail')  
class AddCommentView(CreateView):
    model = Comments
    form_class = CommentForm
    template_name = 'add_comment.html'
    
    def form_valid(self, form):
        form.instance.comment = Post.objects.get(pk=self.kwargs['pk'])
        form.instance.name = self.request.user.username
        response = super().form_valid(form)
        # Create notification
        post = form.instance.comment
        if post.author != self.request.user:  # Don't notify for self-comments
            notification = Notification.objects.create(
                recipient=post.author,
                actor=self.request.user,
                verb='comment',
                target_content_type=ContentType.objects.get_for_model(Post),
                target_object_id=post.id,
            )
            # Send WebSocket notification
            channel_layer = get_channel_layer()
            notification_data = {
                'id': notification.id,
                'actor': notification.actor.username,
                'verb': notification.verb,
                'target': str(notification.target) if notification.target else '',
                'timestamp': notification.timestamp.isoformat(),
                'is_read': notification.is_read,
            }
            async_to_sync(channel_layer.group_send)(
                f'notifications_{post.author.id}',
                {
                    'type': 'send_notification',
                    'notification': notification_data
                }
            )
        return response

    def get_success_url(self):
        return reverse('article-detail', kwargs={'pk': self.kwargs['pk']})
class AddCategoryView(CreateView):
    model = Category
    template_name = 'add_category.html'
    fields = '__all__'


class UpdatePostView(UpdateView):
    model = Post
    template_name = 'update_post.html'
    form_class = EditForm
    # fields = ["title", "title_tag", "body"]
    def form_valid(self, form):
        if 'header_image' in self.request.FILES:
            original_image = self.request.FILES['header_image']  # Get original file
            processed_image = process_image(original_image)      # Process it
            form.instance.header_image = processed_image          # Assign processed file
        return super().form_valid(form)


class DeletePostView(DeleteView):
    model = Post
    template_name = 'delete_post.html'
    success_url = reverse_lazy("home")
    


def search(request):
    if request.method == 'POST':
        searched = request.POST.get('searched')
        # Search by title, snippet, or category
        posts = Post.objects.filter(
            Q(title__icontains=searched) |
            Q(snippet__icontains=searched) |
            Q(category__icontains=searched)
        )
        return render(request, 'search.html', {'searched': searched, 'posts': posts})
    else:
        return render(request, 'search.html', {})
    
def announcements(request):
    announcements = Announcement.objects.all().order_by('-created_at')
    return render(request,"announcements.html",{'announcements':announcements})

def posts(request):
    object_list = Post.objects.all().order_by('-post_date')  # Fetch all posts ordered by date
    return render(request, "posts.html", {'object_list': object_list})  # Pass the posts to the template


from django.views.generic import ListView
from .models import Post, User

class UserPostsView(ListView):
    model = Post
    template_name = 'user_posts.html'
    context_object_name = 'posts'
    paginate_by = 5
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Post.objects.filter(author_id=user_id).order_by('-post_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        context['page_user'] = User.objects.get(id=user_id)
        return context


from django.http import JsonResponse
from .models import Notification
from django.shortcuts import get_object_or_404

def get_notifications(request):
    if request.user.is_authenticated:
        # Clean up old notifications
        Notification.cleanup_old_notifications(request.user)
        
        notifications = Notification.objects.filter(
            recipient=request.user
        ).select_related('actor').order_by('-timestamp')[:10]  # Add select_related for efficiency
        
        data = [{
            'id': n.id,
            'actor': n.actor.username,
            'actor_id': n.actor.id,
            'verb': n.verb,
            'target': str(n.target) if n.target else '',
            'target_id': n.target_object_id if n.target else None,
            'timestamp': n.timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # Format timestamp
            'is_read': n.is_read,
        } for n in notifications]
        return JsonResponse({'notifications': data})
    return JsonResponse({'notifications': []})

def get_unread_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'unread_count': count})
    return JsonResponse({'unread_count': 0})

def mark_notification_read(request, notification_id):
    if request.user.is_authenticated:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        
        # Clean up old notifications
        Notification.cleanup_old_notifications(request.user)
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=403)

def get_recommended_posts(user, limit=20):
    """Generate personalized feed recommendations for a user"""
    if not user.is_authenticated:
        # For anonymous users, return popular posts
        return Post.objects.all().order_by('-likes')[:limit]
    
    # Get posts from followed users (higher weight)
    followed_users = [follow.followed.id for follow in Follow.objects.filter(follower=user)]
    followed_posts = Post.objects.filter(author_id__in=followed_users)
    
    # Get categories user has interacted with
    liked_posts = Post.objects.filter(likes=user)
    commented_posts = Post.objects.filter(comments__name=user.username).distinct()
    
    # Extract categories of interest
    from itertools import chain
    categories_of_interest = set()
    for post in chain(liked_posts, commented_posts):
        categories_of_interest.add(post.category)
    
    # Get posts in categories of interest
    category_posts = Post.objects.filter(category__in=categories_of_interest)
    
    # Combine and deduplicate
    recommended_posts = []
    
    # First priority: posts from followed users (most recent)
    for post in followed_posts.order_by('-post_date')[:limit//2]:
        if post not in recommended_posts and post.author != user:
            recommended_posts.append(post)
    
    # Second priority: posts in categories of interest
    for post in category_posts.order_by('-post_date'):
        if post not in recommended_posts and post.author != user:
            recommended_posts.append(post)
            if len(recommended_posts) >= limit:
                break
    
    # If we still need more posts, add popular posts
    if len(recommended_posts) < limit:
        popular_posts = Post.objects.all().order_by('-post_date')
        for post in popular_posts:
            if post not in recommended_posts and post.author != user:
                recommended_posts.append(post)
                if len(recommended_posts) >= limit:
                    break
    
    return recommended_posts

class FeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'feed.html'
    context_object_name = 'posts'
    
    def get_queryset(self):
        return get_recommended_posts(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_menu'] = Category.objects.all()
        
        # Add liked_posts to context
        if self.request.user.is_authenticated:
            context['liked_post_ids'] = list(self.request.user.blog_posts.values_list('id', flat=True))
        else:
            context['liked_post_ids'] = []
            
        return context

def track_post_view(request, pk):
    """Track when a user views a post"""
    if request.user.is_authenticated:
        post = get_object_or_404(Post, pk=pk)
        interaction, created = UserInteraction.objects.get_or_create(
            user=request.user,
            post=post
        )
        if not created:
            # Update the view timestamp
            interaction.viewed_at = timezone.now()
            interaction.save()
    
    # Return JSON response for AJAX calls
    return JsonResponse({'success': True})


    
    
    