import re
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages  
from django.core.mail import EmailMessage, send_mail
from rest_framework import generics
from .forms import ContactForm
from django.conf import settings
from django.urls import reverse_lazy
from django.core.validators import ValidationError
import numpy as np
from members.forms import ProfilePageForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.generic import DetailView, CreateView,ListView
from django.views import generic
from blog.models import Follow, Profile
from blog.views import process_image
from .tokens import generate_token
from fuzzywuzzy import fuzz
from decimal import Decimal
from rest_framework import generics
from django.db import models
from django.db.models import Q
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from blog.models import Follow


def get_started(request):
    return render(request, 'authentication/get_started.html')


def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['firstname']
        lname = request.POST['lastname']
        email = request.POST['email']
        pass1 = request.POST['password']
        pass2 = request.POST['confirmpassword']

        errors = {}  # Dictionary to store field-specific errors

        # Check for existing username
        if User.objects.filter(username=username).exists():
            errors['username'] = "Username already exists! Please try another username."

        # Check for existing email
        if User.objects.filter(email=email).exists():
            errors['email'] = "Email already registered!"

        # Validate username length
        if len(username) > 20:
            errors['username'] = "Username must be under 20 characters!"

        # Validate password match
        if pass1 != pass2:
            errors['password'] = "Passwords didn't match!"
            errors['confirmpassword'] = "Passwords didn't match!"

        # Validate password length
        if len(pass1) < 8:
            errors['password'] = "Password must be at least 8 characters long!"

        # Validate password complexity
        if not re.search(r"[A-Z]", pass1):
            errors['password'] = "Password must contain at least one uppercase letter!"
        elif not re.search(r"[a-z]", pass1):
            errors['password'] = "Password must contain at least one lowercase letter!"
        elif not re.search(r"[0-9]", pass1):
            errors['password'] = "Password must contain at least one digit!"
        elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pass1):
            errors['password'] = "Password must contain at least one special character!"

        # Validate username is alphanumeric
        if not username.isalnum():
            errors['username'] = "Username must be alphanumeric!"

        # If there are errors, re-render the signup page with form data and errors
        if errors:
            return render(request, "authentication/signup.html", {
                'errors': errors,
                'form_data': request.POST  # Pass the current form data
            })

        # Create user
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False  # User is not active until verified
        myuser.save()

        messages.success(request, "Your account has been created successfully! Please check your email to confirm your account.")

        # Send Welcome Email
        subject = "Welcome to GFG - Django Login!"
        message = f"Hello {myuser.first_name}!! \nWelcome to GFG!! \nThank you for visiting our website. We have also sent you a confirmation email, please confirm your email address."
        send_mail(subject, message, settings.EMAIL_HOST_USER, [myuser.email], fail_silently=True)

        # Send Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirm your Email @ GFG - Django Login!"
        message2 = render_to_string('email_confirmation.html', {
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = False
        email.send()

        return redirect('verification_message')  # Redirect to the verification message page

    return render(request, "authentication/signup.html")

def verification_message(request):
    return render(request, "authentication/verification_message.html")
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        # user.profile.signup_confirmation = True
        myuser.save()
        login(request, myuser)
        messages.success(request, "Your Account has been activated!!")
        return redirect('signin')
    else:
        return render(request, 'activation_failed.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['password']

        user = authenticate(username=username, password=pass1)

        if user is not None:
            login(request, user)
            # messages.success(request, "Logged In Sucessfully!!")
            return redirect('home')
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect('signin')

    return render(request, "authentication/signin.html")


def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')


def password_reset_request(request):
    if request.method == "POST":
        email = request.POST['email']
        user = User.objects.filter(email=email).first()
        if user:
            current_site = get_current_site(request)
            email_subject = "Password Reset Request"
            message = render_to_string('password_reset_email.html', {
                'email': user.email,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': generate_token.make_token(user),
            })
            email = EmailMessage(
                email_subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
            )
            try:
                email.send(fail_silently=False)  # Set to False to raise errors
                messages.success(request, "A link to reset your password has been sent to your email.")
            except Exception as e:
                messages.error(request, f"Error sending email: {str(e)}")
        else:
            messages.error(request, "Email address not found.")

    return render(request, "authentication/password_reset.html")


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST['new_password']
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, "Your password has been reset successfully!")
            return redirect('signin')

        return render(request, 'authentication/password_reset_confirm.html', {'validlink': True})

    else:
        messages.error(request, "The password reset link is invalid.")
        return render(request, 'authentication/password_reset_confirm.html', {'validlink': False})


def edit_profile(request):
    user = request.user  # Get the currently logged-in user

    if request.method == 'POST':
        username = request.POST.get('username', user.username)
        first_name = request.POST.get('firstname', user.first_name)
        last_name = request.POST.get('lastname', user.last_name)
        email = request.POST.get('email', user.email)

        # Update the user instance
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        # Save the changes
        user.save()
        messages.success(request, "Your profile has been updated successfully!")
        return redirect('edit_profile')  # Redirect to the same page or another page

    # For GET request, render the form with current user details
    context = {
        'username': user.username,
        'firstname': user.first_name,
        'lastname': user.last_name,
        'email': user.email,
    }
    return render(request, 'authentication/edit_profile.html', context)


class ShowProfilePageView(DetailView):
    model = Profile
    template_name = "authentication/user_profile.html"

    def get_context_data(self, *args, **kwargs):
        context = super(ShowProfilePageView, self).get_context_data(*args, **kwargs)
        page_user = get_object_or_404(Profile, id=self.kwargs['pk'])
        
        # Get follow counts
        followers_count = page_user.user.followers.count()
        following_count = page_user.user.following.count()
        
        # Check if the viewing user is following this profile
        is_following = False
        is_followed_by = False
        
        if self.request.user.is_authenticated and self.request.user != page_user.user:
            is_following = Follow.objects.filter(follower=self.request.user, followed=page_user.user).exists()
            is_followed_by = Follow.objects.filter(follower=page_user.user, followed=self.request.user).exists()
        
        context["page_user"] = page_user
        context["followers_count"] = followers_count
        context["following_count"] = following_count
        context["is_following"] = is_following
        context["is_followed_by"] = is_followed_by
        
        return context


class EditProfilePageView(generic.UpdateView):
    model = Profile
    fields = ['bio', 'profile_pic', 'website_url', 'linkedin_url', 'facebook_url', 'twitter_url', 'instagram_url',
              'pinterest_url']
    template_name = "authentication/edit_profile_page.html"
    success_url = reverse_lazy("home")
    def form_valid(self, form):
        if 'profile_pic' in self.request.FILES:
            original_image = self.request.FILES['profile_pic']  # Get original file
            processed_image = process_image(original_image)      # Process it
            form.instance.profile_pic = processed_image          # Assign processed file
        return super().form_valid(form)


class CreateProfilePageView(CreateView):
    model = Profile
    form_class = ProfilePageForm
    template_name = "authentication/create_user_profile_page.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        if 'profile_pic' in self.request.FILES:
            original_image = self.request.FILES['profile_pic']  # Get original file
            processed_image = process_image(original_image)      # Process it
            form.instance.profile_pic = processed_image          # Assign processed file
        return super().form_valid(form)


def onboarding(request):
    # Ensure the user is authenticated and email is verified
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to access this page.")
        return redirect('signin')

    if not request.user.is_active:
        messages.error(request, "Please verify your email to access this page.")
        return redirect('verification_message')

    if request.method == 'POST':
        # Retrieve and validate user type
        user_type = request.POST.get('user_type', None)
        if not user_type:
            messages.error(request, "Please select a user type.")
            return render(request, 'authentication/onboarding.html')

        # Common fields for all users
        region = request.POST.get('region', '').strip()
        estimated_income = request.POST.get('estimated_income', '0').strip()
        fee_affordability = request.POST.get('fee_affordability', '0').strip()
        dream_career = request.POST.get('dream_career', '').strip()
        language = request.POST.get('language', '').strip()
        program_type = request.POST.get('program_type', '').strip() #Added program_type

        # Validate numeric fields
        try:
            estimated_income = float(estimated_income) if estimated_income else None
            fee_affordability = float(fee_affordability) if fee_affordability else None
        except ValueError:
            messages.error(request, "Estimated Income and Fee Affordability must be numbers.")
            return render(request, 'authentication/onboarding.html')

        # Create a new Profile object
        profile = Profile(
            user=request.user,
            user_type=user_type,
            region=region,
            estimated_income=estimated_income,
            fee_affordability=fee_affordability,
            dream_career=dream_career,
            language=language,
            program_type = program_type #added program_type
        )

        try:
            # Additional fields based on user type
            if user_type == 'dropout':
                profile.learning_goal = request.POST.get('learning_goal', '').strip()
            elif user_type == 'high_school':
                profile.series = request.POST.get('series', '').strip()
                profile.best_subject = request.POST.get('best_subject', '').strip()
                profile.language = request.POST.get('language', '').strip()
                profile.extracurriculars = request.POST.get('extracurriculars', '').strip()
                profile.skills_to_develop = request.POST.get('skills_to_develop', '').strip()
            elif user_type == 'university':
                profile.major = request.POST.get('major', '').strip()
                profile.intended_study_field = request.POST.get('intended_study_field', '').strip()
                profile.skills_to_develop = request.POST.get('skills_to_develop', '').strip()
            elif user_type == 'worker':
                profile.job_title = request.POST.get('job_title', '').strip()
                profile.industry = request.POST.get('industry', '').strip()
                profile.specific_skills = request.POST.get('specific_skills', '').strip()
                profile.extracurricular_activities = request.POST.get('extracurricular_activities', '').strip()

            # Save the profile
            profile.save()
            messages.success(request, "Your profile has been created successfully!")
            return redirect('home')

        except Exception as e:
            messages.error(request, f"An error occurred while saving your profile: {e}")
            return render(request, 'authentication/onboarding.html')

    return render(request, 'authentication/onboarding.html')




import logging

# Set up logging (optional, for debugging)
logger = logging.getLogger(__name__)

def terms_and_conditions(request):
    return render(request, 'authentication/terms_and_conditions.html') 

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data.get('phone', 'N/A')
            subject = form.cleaned_data.get('subject', 'N/A')
            message = form.cleaned_data['message']

            send_mail(
                subject=f"Contact Form: {subject}",
                message=f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.RECIPIENT_EMAIL],
                fail_silently=False,
            )

            return redirect('members:contact_success')
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})

def contact_success(request):
    return render(request, 'contact_success.html')



from django.contrib.contenttypes.models import ContentType
from blog.models import Notification

class FollowUserView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user_to_follow = get_object_or_404(User, id=self.kwargs['pk'])
        
        if request.user == user_to_follow:
            messages.error(request, "You cannot follow yourself.")
            return redirect('show_profile_page', pk=user_to_follow.profile.id)
        
        follow_exists = Follow.objects.filter(follower=request.user, followed=user_to_follow).exists()
        
        if not follow_exists:
            Follow.objects.create(follower=request.user, followed=user_to_follow)
            # Create notification
            Notification.objects.create(
                recipient=user_to_follow,
                actor=request.user,
                verb='follow',
            )
            messages.success(request, f"You are now following {user_to_follow.username}.")
        
        return redirect('show_profile_page', pk=user_to_follow.profile.id)
class UnfollowUserView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user_to_unfollow = get_object_or_404(User, id=self.kwargs['pk'])
        
        # Delete the follow relationship if it exists
        Follow.objects.filter(follower=request.user, followed=user_to_unfollow).delete()
        messages.success(request, f"You have unfollowed {user_to_unfollow.username}.")
        
        # Redirect back to the profile page
        return redirect('show_profile_page', pk=user_to_unfollow.profile.id)
    
    
class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'authentication/user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        return User.objects.exclude(id=self.request.user.id).prefetch_related('profile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get list of users the current user is following
        following_ids = self.request.user.following.values_list('followed_id', flat=True)
        # Get list of users following the current user
        followers_ids = self.request.user.followers.values_list('follower_id', flat=True)
        
        context['following_ids'] = following_ids
        context['followers_ids'] = followers_ids
        
        return context

class FollowersListView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'authentication/followers_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get followers
        followers = Follow.objects.filter(followed=user).select_related('follower__profile')
        
        # Get list of users the current user is following
        following_ids = self.request.user.following.values_list('followed_id', flat=True)
        
        context['user_profile'] = user.profile
        context['followers'] = followers
        context['following_ids'] = following_ids
        
        return context

class FollowingListView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'authentication/following_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get following
        following = Follow.objects.filter(follower=user).select_related('followed__profile')
        
        # Get list of users the current user is following
        following_ids = self.request.user.following.values_list('followed_id', flat=True)
        
        context['user_profile'] = user.profile
        context['following'] = following
        context['following_ids'] = following_ids
        
        return context