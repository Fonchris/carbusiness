

from django import forms
from .models import Comments, Post, Category
from django_ckeditor_5.fields import CKEditor5Field

def get_category_choices():
    try:
        choices = Category.objects.all().values_list("name", "name")
        return choices
    except:
        return []

class PostForm(forms.ModelForm):
    body = CKEditor5Field('Text', config_name='extends')

    class Meta:
        model = Post
        fields = ("title", "title_tag", "category", "body", "snippet", "header_image")

        widgets = {
            "title": forms.TextInput(attrs={'class': 'form-control'}),
            "title_tag": forms.TextInput(attrs={'class': 'form-control'}),
            "category": forms.Select(choices=get_category_choices, attrs={'class': 'form-control'}),
            "snippet": forms.Textarea(attrs={'class': 'form-control'}),
        }

class EditForm(forms.ModelForm):
    body = CKEditor5Field('Text', config_name='extends')

    class Meta:
        model = Post
        fields = ("title", "title_tag", "category", "body", "snippet")

        widgets = {
            "title": forms.TextInput(attrs={'class': 'form-control'}),
            "title_tag": forms.TextInput(attrs={'class': 'form-control'}),
            "category": forms.Select(choices=get_category_choices, attrs={'class': 'form-control'}),
            "snippet": forms.Textarea(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ("body",)

        widgets = {
            "body": forms.Textarea(attrs={'class': 'form-control'}),
        }

class SearchForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("body",)

        widgets = {
            "body": forms.Textarea(attrs={'class': 'form-control'}),
        }