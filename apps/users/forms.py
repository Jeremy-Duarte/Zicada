from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm as BaseUserChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from apps.core.crud.mixins import FormStyleMixin

User = get_user_model()

# =============================================================================
# CONSTANTES DE FORMULARIOS
# =============================================================================

PHONE_PLACEHOLDER = 'Ej: 3001234567'
EMAIL_PLACEHOLDER = 'correo@ejemplo.com'
FIRST_NAME_PLACEHOLDER = 'Nombre'
LAST_NAME_PLACEHOLDER = 'Apellido'
CURRENT_PASSWORD_PLACEHOLDER = 'Ingresa tu contraseña actual'
NEW_PASSWORD_PLACEHOLDER = 'Nueva contraseña'
CONFIRM_PASSWORD_PLACEHOLDER = 'Confirma tu nueva contraseña'

ERROR_PHONE_MIN_DIGITS = 'El teléfono debe tener al menos 7 dígitos.'
ERROR_PHONE_MAX_DIGITS = 'El teléfono no puede tener más de 15 dígitos.'
ERROR_PHONE_DUPLICATE = 'Este número de teléfono ya está registrado por otro usuario.'

ERROR_PASSWORD_MIN_LENGTH = 'La contraseña debe tener al menos 8 caracteres.'
ERROR_PASSWORD_NUMERIC_ONLY = 'La contraseña no puede ser completamente numérica.'
ERROR_PASSWORD_COMMON = 'La contraseña es demasiado común.'
ERROR_PASSWORD_MISMATCH = 'Las contraseñas no coinciden.'
ERROR_PASSWORD_SAME_AS_CURRENT = 'La nueva contraseña no puede ser igual a la actual.'
ERROR_CURRENT_PASSWORD_INCORRECT = 'La contraseña actual es incorrecta.'

ERROR_USER_NOT_SPECIFIED = 'Usuario no especificado.'
ERROR_USERNAME_EXISTS = 'Ya existe un usuario con ese nombre de usuario.'
ERROR_EMAIL_EXISTS = 'Ya existe un usuario con ese correo electrónico.'
ERROR_USER_ALREADY_ACTIVE = 'Este usuario ya está activo.'
ERROR_CANNOT_DISABLE_LAST_SUPERUSER = 'No se puede desactivar el único superusuario del sistema.'
ERROR_USERNAME_MISMATCH = 'El nombre de usuario no coincide.'

ERROR_GROUP_NOT_SPECIFIED = 'Rol no especificado.'
ERROR_GROUP_NAME_EXISTS = 'Ya existe un rol con ese nombre.'
ERROR_GROUP_NAME_RESERVED = 'El nombre "{name}" está reservado para grupos del sistema.'
ERROR_GROUP_HAS_USERS = 'No se puede eliminar este rol porque tiene {count} usuario(s) asignado(s). Reasigna o elimina esos usuarios primero.'
ERROR_GROUP_PROTECTED = 'No se puede eliminar el rol "{name}" porque es un rol del sistema.'

LABEL_NEW_PASSWORD = 'Nueva contraseña'
LABEL_CONFIRM_PASSWORD = 'Confirmar contraseña'
LABEL_CURRENT_PASSWORD = 'Contraseña actual'

PROTECTED_GROUP_NAMES = ['admin', 'staff', 'delivery']
COMMON_PASSWORDS = ['password', '12345678', 'qwerty123']


class UserCreateForm(FormStyleMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'is_delivery', 'is_active', 'is_staff', 'is_superuser', 'groups',
        ]
        widgets = {
            'username': forms.TextInput(),
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput(),
            'email': forms.EmailInput(),
            'phone': forms.TextInput(attrs={'placeholder': PHONE_PLACEHOLDER}),
            'is_delivery': forms.CheckboxInput(),
            'is_active': forms.CheckboxInput(),
            'is_staff': forms.CheckboxInput(),
            'is_superuser': forms.CheckboxInput(),
            'groups': forms.SelectMultiple(attrs={'size': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput()
        self.fields['password2'].widget = forms.PasswordInput()
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = LABEL_CONFIRM_PASSWORD
        self.fields['groups'].queryset = Group.objects.all().order_by('name')
        self.fields['groups'].help_text = 'Roles asignados al usuario'
    
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(ERROR_USERNAME_EXISTS)
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError(ERROR_EMAIL_EXISTS)
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            digits = ''.join(c for c in phone if c.isdigit())
            if len(digits) < 7:
                raise ValidationError(ERROR_PHONE_MIN_DIGITS)
            if len(digits) > 15:
                raise ValidationError(ERROR_PHONE_MAX_DIGITS)
            return digits
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_superuser') and not cleaned_data.get('is_staff'):
            cleaned_data['is_staff'] = True
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if user.is_superuser and not user.is_staff:
            user.is_staff = True
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserUpdateForm(FormStyleMixin, BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'is_delivery', 'is_active', 'is_staff', 'is_superuser', 'groups',
        ]
        widgets = {
            'username': forms.TextInput(),
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput(),
            'email': forms.EmailInput(),
            'phone': forms.TextInput(attrs={'placeholder': PHONE_PLACEHOLDER}),
            'is_delivery': forms.CheckboxInput(),
            'is_active': forms.CheckboxInput(),
            'is_staff': forms.CheckboxInput(),
            'is_superuser': forms.CheckboxInput(),
            'groups': forms.SelectMultiple(attrs={'size': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].queryset = Group.objects.all().order_by('name')
        if self.instance and self.instance.pk and self.instance.is_superuser:
            if User.objects.filter(is_superuser=True).count() == 1:
                self.fields['is_superuser'].disabled = True
                self.fields['is_superuser'].help_text = 'No puedes desactivar el único superusuario del sistema.'
    
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        qs = User.objects.filter(username__iexact=username)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(ERROR_USERNAME_EXISTS)
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if email and qs.exists():
            raise ValidationError(ERROR_EMAIL_EXISTS)
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            digits = ''.join(c for c in phone if c.isdigit())
            if len(digits) < 7:
                raise ValidationError(ERROR_PHONE_MIN_DIGITS)
            if len(digits) > 15:
                raise ValidationError(ERROR_PHONE_MAX_DIGITS)
            return digits
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_superuser'):
            cleaned_data['is_staff'] = True
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if user.is_superuser and not user.is_staff:
            user.is_staff = True
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserChangePasswordForm(FormStyleMixin, forms.Form):
    password1 = forms.CharField(
        label=LABEL_NEW_PASSWORD,
        widget=forms.PasswordInput(),
        required=True,
        min_length=8,
    )
    password2 = forms.CharField(
        label=LABEL_CONFIRM_PASSWORD,
        widget=forms.PasswordInput(),
        required=True,
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if len(password) < 8:
            raise ValidationError(ERROR_PASSWORD_MIN_LENGTH)
        if password.isdigit():
            raise ValidationError(ERROR_PASSWORD_NUMERIC_ONLY)
        if password.lower() in COMMON_PASSWORDS:
            raise ValidationError(ERROR_PASSWORD_COMMON)
        return password
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(ERROR_PASSWORD_MISMATCH)
        return password2
    
    def clean(self):
        cleaned_data = super().clean()
        if not self.user:
            raise ValidationError(ERROR_USER_NOT_SPECIFIED)
        return cleaned_data
    
    def save(self):
        password = self.cleaned_data.get('password1')
        self.user.set_password(password)
        self.user.save(update_fields=['password'])
        return self.user


class UserDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre de usuario para confirmar',
        widget=forms.TextInput(attrs={'placeholder': 'Ej: juan.perez'})
    )
    reassign_content = forms.BooleanField(
        required=False,
        label='Reasignar contenido creado por este usuario',
        help_text='Si está activado, el contenido creado por este usuario se reasignará al usuario administrador.'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').strip().lower()
        if not self.user:
            raise ValidationError(ERROR_USER_NOT_SPECIFIED)
        if self.user.username.lower() != value:
            raise ValidationError(ERROR_USERNAME_MISMATCH)
        if self.user.is_superuser and User.objects.filter(is_superuser=True).count() == 1:
            raise ValidationError(ERROR_CANNOT_DISABLE_LAST_SUPERUSER)
        return value


class UserRestoreForm(FormStyleMixin, forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que deseo reactivar este usuario'
    )
    send_notification = forms.BooleanField(
        required=False,
        initial=True,
        label='Enviar notificación al usuario',
        help_text='Enviar un correo informando que su cuenta ha sido reactivada.'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        if not self.user:
            raise ValidationError(ERROR_USER_NOT_SPECIFIED)
        if self.user.is_active:
            raise ValidationError(ERROR_USER_ALREADY_ACTIVE)
        if User.objects.filter(username__iexact=self.user.username).exclude(pk=self.user.pk).exists():
            raise ValidationError('Ya existe un usuario activo con este nombre de usuario.')
        if self.user.email and User.objects.filter(email__iexact=self.user.email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Ya existe un usuario activo con este correo electrónico.')
        if not cleaned_data.get('confirm'):
            raise ValidationError('Debes confirmar la reactivación.')
        return cleaned_data


class GroupCreateForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {'name': forms.TextInput()}
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if Group.objects.filter(name__iexact=name).exists():
            raise ValidationError(ERROR_GROUP_NAME_EXISTS)
        return name


class GroupUpdateForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {'name': forms.TextInput()}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_name = self.instance.name if self.instance else ''
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs = Group.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(ERROR_GROUP_NAME_EXISTS)
        if name.lower() in PROTECTED_GROUP_NAMES and self.original_name.lower() != name.lower():
            raise ValidationError(ERROR_GROUP_NAME_RESERVED.format(name=name))
        return name


class GroupDeleteForm(FormStyleMixin, forms.Form):
    confirm = forms.CharField(
        required=True,
        label='Escribe el nombre del rol para confirmar',
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Editores'})
    )
    
    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
    
    def clean_confirm(self):
        value = self.cleaned_data.get('confirm', '').strip().lower()
        if not self.group:
            raise ValidationError(ERROR_GROUP_NOT_SPECIFIED)
        if self.group.name.lower() != value:
            raise ValidationError('El nombre del rol no coincide.')
        if self.group.name.lower() in PROTECTED_GROUP_NAMES:
            raise ValidationError(ERROR_GROUP_PROTECTED.format(name=self.group.name))
        user_count = self.group.user_set.count()
        if user_count > 0:
            raise ValidationError(ERROR_GROUP_HAS_USERS.format(count=user_count))
        return value


class UserProfileForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': FIRST_NAME_PLACEHOLDER}),
            'last_name': forms.TextInput(attrs={'placeholder': LAST_NAME_PLACEHOLDER}),
            'email': forms.EmailInput(attrs={'placeholder': EMAIL_PLACEHOLDER}),
            'phone': forms.TextInput(attrs={'placeholder': PHONE_PLACEHOLDER}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['email'].required = False
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone:
            digits = ''.join(c for c in phone if c.isdigit())
            if len(digits) < 7:
                raise ValidationError(ERROR_PHONE_MIN_DIGITS)
            if len(digits) > 15:
                raise ValidationError(ERROR_PHONE_MAX_DIGITS)
            qs = User.objects.filter(phone=digits)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(ERROR_PHONE_DUPLICATE)
            return digits
        return ''
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email:
            qs = User.objects.filter(email__iexact=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(ERROR_EMAIL_EXISTS)
        return email


class UserProfilePasswordForm(FormStyleMixin, forms.Form):
    current_password = forms.CharField(
        label=LABEL_CURRENT_PASSWORD,
        widget=forms.PasswordInput(attrs={'placeholder': CURRENT_PASSWORD_PLACEHOLDER}),
        required=True
    )
    new_password1 = forms.CharField(
        label=LABEL_NEW_PASSWORD,
        widget=forms.PasswordInput(attrs={'placeholder': NEW_PASSWORD_PLACEHOLDER}),
        required=True,
        min_length=8
    )
    new_password2 = forms.CharField(
        label=LABEL_CONFIRM_PASSWORD,
        widget=forms.PasswordInput(attrs={'placeholder': CONFIRM_PASSWORD_PLACEHOLDER}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if self.user and not self.user.check_password(current_password):
            raise ValidationError(ERROR_CURRENT_PASSWORD_INCORRECT)
        return current_password
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1', '')
        if len(password) < 8:
            raise ValidationError(ERROR_PASSWORD_MIN_LENGTH)
        if password.isdigit():
            raise ValidationError(ERROR_PASSWORD_NUMERIC_ONLY)
        if password.lower() in COMMON_PASSWORDS:
            raise ValidationError(ERROR_PASSWORD_COMMON)
        if self.user and self.user.check_password(password):
            raise ValidationError(ERROR_PASSWORD_SAME_AS_CURRENT)
        return password
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(ERROR_PASSWORD_MISMATCH)
        return password2
    
    def save(self):
        password = self.cleaned_data.get('new_password1')
        self.user.set_password(password)
        self.user.save(update_fields=['password'])
        return self.user


class DeliveryUserProfileForm(FormStyleMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': PHONE_PLACEHOLDER}),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = ''.join(c for c in phone if c.isdigit())
        if len(digits) < 7:
            raise ValidationError(ERROR_PHONE_MIN_DIGITS)
        if len(digits) > 15:
            raise ValidationError(ERROR_PHONE_MAX_DIGITS)
        return digits