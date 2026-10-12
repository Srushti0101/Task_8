from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Task


class StyledFormMixin:
    """Adds a CSS class (and placeholder) to every widget."""

    def style_fields(self):
        for field in self.fields.values():
            css = 'input'
            if isinstance(field.widget, forms.Select):
                css = 'input select'
            field.widget.attrs.setdefault('class', css)
            if not isinstance(field.widget, (forms.Select, forms.DateInput)):
                field.widget.attrs.setdefault('placeholder', field.label)


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields['username'].widget.attrs.update(autofocus=True, placeholder='Username')
        self.fields['password'].widget.attrs.update(placeholder='Password')


class RegisterForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Confirm password'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm password'
        self.fields['username'].help_text = ''
        self.fields['password2'].help_text = ''

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class TaskForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
