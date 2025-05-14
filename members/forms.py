from django import forms
from blog.models import Profile
class ProfilePageForm(forms.ModelForm):
    class Meta:
        
       model = Profile
       fields = ('bio','profile_pic','website_url','linkedin_url','facebook_url','twitter_url','instagram_url','pinterest_url')
       widgets = {
            "bio": forms.Textarea(attrs={'class': 'form-control'}),
            "profile_pic": forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            #"profile_pic": forms.TextInput(attrs={'class': 'form-control'}),
            "website_url": forms.TextInput(attrs={'class': 'form-control'}),
            "linkedin_url": forms.TextInput(attrs={'class': 'form-control'}),
            "facebook_url": forms.TextInput(attrs={'class': 'form-control'}),
            "twitter_url": forms.TextInput(attrs={'class': 'form-control'}),
            "instagram_url": forms.TextInput(attrs={'class': 'form-control'}),
            "pinterest_url": forms.TextInput(attrs={'class': 'form-control'}),
        }
       

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    subject = forms.CharField(max_length=200, required=False)
    message = forms.CharField(widget=forms.Textarea)
