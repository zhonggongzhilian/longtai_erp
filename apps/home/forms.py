# myapp/forms.py

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Username",
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Password",
                "class": "form-control"
            }
        ))


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "用户名",
                "class": "form-control"
            }
        )
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "手机号",
                "class": "form-control"
            }
        )
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,  # 确保引用模型中的 ROLE_CHOICES
        widget=forms.Select(
            attrs={
                "class": "form-control"
            }
        )
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "密码",
                "class": "form-control"
            }
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "确认密码",
                "class": "form-control"
            }
        )
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'role', 'password1', 'password2')

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        if commit:
            user.email = 'default@example.com'  # 设置默认邮箱
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'phone_number', 'role', 'is_active', 'is_staff', 'is_superuser')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'role')


from django import forms
from .models import OrderProcessingResult


class TaskForm(forms.ModelForm):
    class Meta:
        model = OrderProcessingResult
        fields = [
            'execution_time',
            'completion_time',
            'order',
            'product',
            'process_sequence',
            'process_name',
            'device'
        ]
        widgets = {
            'execution_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'completion_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['execution_time'].widget.attrs.update({'class': 'form-control'})
        self.fields['completion_time'].widget.attrs.update({'class': 'form-control'})
        self.fields['order'].widget.attrs.update({'class': 'form-control'})
        self.fields['product'].widget.attrs.update({'class': 'form-control'})
        self.fields['process_sequence'].widget.attrs.update({'class': 'form-control'})
        self.fields['process_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['device'].widget.attrs.update({'class': 'form-control'})
