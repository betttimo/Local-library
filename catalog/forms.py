import datetime

from django import forms
from django.contrib.auth.models import User
from .models import BookInstance, Member

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text="Enter a date between now and 4 weeks (default 3):")

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))
        return data
    
class IssueBookForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=True, label="Select User")
    book_instance = forms.ModelChoiceField(queryset=BookInstance.objects.filter(status='a'), required=True, label="Select Book")

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with that username already exists.')
        return username

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['outstanding_debt']

class BookInstanceForm(forms.ModelForm):
    class Meta:
        model = BookInstance
        fields = '__all__'