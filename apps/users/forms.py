from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm as BaseUserChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from apps.core.crud.mixins import FormStyleMixin

User = get_user_model()


# ========== USER FORMS ==========

class UserCreateForm(FormStyleMixin, UserCreationForm):
    """
    Formulario para crear usuarios desde backoffice.
    Hereda de UserCreationForm de Django para manejar contraseñas.
    """
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'is_delivery',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
        ]
        widgets = {
            'username': forms.TextInput(),
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput(),
            'email': forms.EmailInput(),
            'phone': forms.TextInput(attrs={'placeholder': 'Ej: 3001234567'}),
            'is_delivery': forms.CheckboxInput(),
            'is_active': forms.CheckboxInput(),
            'is_staff': forms.CheckboxInput(),
            'is_superuser': forms.CheckboxInput(),
            'groups': forms.SelectMultiple(attrs={'size': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar widgets de contraseña
        self.fields['password1'].widget = forms.PasswordInput()
        self.fields['password2'].widget = forms.PasswordInput()
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        
        # Limitar grupos disponibles (excluir grupos del sistema si es necesario)
        self.fields['groups'].queryset = Group.objects.all().order_by('name')
        self.fields['groups'].help_text = 'Roles asignados al usuario'
    
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Ya existe un usuario con ese nombre de usuario.')
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Ya existe un usuario con ese correo electrónico.')
        
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        
        if phone:
            digits = ''.join(c for c in phone if c.isdigit())
            
            if len(digits) < 7:
                raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
            
            if len(digits) > 15:
                raise ValidationError('El teléfono no puede tener más de 15 dígitos.')
            
            return digits
        
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Superusers must be staff (for admin access)
        if cleaned_data.get('is_superuser') and not cleaned_data.get('is_staff'):
            cleaned_data['is_staff'] = True
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Enforce staff for superuser again at save time
        if user.is_superuser and not user.is_staff:
            user.is_staff = True
        
        if commit:
            user.save()
            self.save_m2m()
        
        return user


class UserUpdateForm(FormStyleMixin, BaseUserChangeForm):
    """
    Formulario para actualizar usuarios desde backoffice.
    No maneja cambio de contraseña (eso va en formulario aparte).
    """
    
    class Meta(BaseUserChangeForm.Meta):
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'is_delivery',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
        ]
        widgets = {
            'username': forms.TextInput(),
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput(),
            'email': forms.EmailInput(),
            'phone': forms.TextInput(attrs={'placeholder': 'Ej: 3001234567'}),
            'is_delivery': forms.CheckboxInput(),
            'is_active': forms.CheckboxInput(),
            'is_staff': forms.CheckboxInput(),
            'is_superuser': forms.CheckboxInput(),
            'groups': forms.SelectMultiple(attrs={'size': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].queryset = Group.objects.all().order_by('name')
        
        # Deshabilitar campos para que un usuario no pueda modificarse a sí mismo
        # (esto se maneja en la vista)
        
        # Si el usuario es superusuario y es el único, no permitir quitar superuser
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
            raise ValidationError('Ya existe un usuario con ese nombre de usuario.')
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email__iexact=email)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if email and qs.exists():
            raise ValidationError('Ya existe un usuario con ese correo electrónico.')
        
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        
        if phone:
            digits = ''.join(c for c in phone if c.isdigit())
            
            if len(digits) < 7:
                raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
            
            if len(digits) > 15:
                raise ValidationError('El teléfono no puede tener más de 15 dígitos.')
            
            return digits
        
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        
        is_superuser = cleaned_data.get('is_superuser')
        is_staff = cleaned_data.get('is_staff')
        
        if is_superuser:
            # Staff is implicit; cleaned_data key is informational only.
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
    """
    Formulario específico para cambiar contraseña de usuario.
    """
    
    password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(),
        required=True,
        min_length=8,
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(),
        required=True,
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        # Validaciones adicionales
        if password.isdigit():
            raise ValidationError('La contraseña no puede ser completamente numérica.')
        
        if password.lower() in ['password', '12345678', 'qwerty123']:
            raise ValidationError('La contraseña es demasiado común.')
        
        return password
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        
        return password2
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.user:
            raise ValidationError('Usuario no especificado.')
        
        return cleaned_data
    
    def save(self):
        """
        Guarda la nueva contraseña.
        """
        password = self.cleaned_data.get('password1')
        self.user.set_password(password)
        self.user.save(update_fields=['password'])
        return self.user


class UserDeleteForm(FormStyleMixin, forms.Form):
    """
    Formulario para desactivar usuario (soft delete equivalente).
    Django no tiene soft delete built-in, usamos is_active=False.
    """
    
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
            raise ValidationError('Usuario no especificado.')
        
        if self.user.username.lower() != value:
            raise ValidationError('El nombre de usuario no coincide.')
        
        # No permitir desactivar el propio usuario
        # (esto se valida mejor en la vista con request.user)
        
        # No permitir desactivar el único superusuario
        if self.user.is_superuser and User.objects.filter(is_superuser=True).count() == 1:
            raise ValidationError('No se puede desactivar el único superusuario del sistema.')
        
        return value


class UserRestoreForm(FormStyleMixin, forms.Form):
    """
    Formulario para restaurar usuario (reactivar is_active).
    """
    
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
            raise ValidationError('Usuario no especificado.')
        
        if self.user.is_active:
            raise ValidationError('Este usuario ya está activo.')
        
        # Verificar conflictos (username, email)
        if User.objects.filter(username__iexact=self.user.username).exclude(pk=self.user.pk).exists():
            raise ValidationError('Ya existe un usuario activo con este nombre de usuario.')
        
        if self.user.email and User.objects.filter(email__iexact=self.user.email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Ya existe un usuario activo con este correo electrónico.')
        
        confirm = cleaned_data.get('confirm')
        if not confirm:
            raise ValidationError('Debes confirmar la reactivación.')
        
        return cleaned_data


# ========== GROUP (ROLE) FORMS ==========

class GroupCreateForm(FormStyleMixin, forms.ModelForm):
    """
    Formulario para crear grupos/roles.
    """
    
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        
        if Group.objects.filter(name__iexact=name).exists():
            raise ValidationError('Ya existe un rol con ese nombre.')
        
        return name


class GroupUpdateForm(FormStyleMixin, forms.ModelForm):
    """
    Formulario para actualizar grupos/roles.
    """
    
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_name = self.instance.name if self.instance else ''
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs = Group.objects.filter(name__iexact=name)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Ya existe un rol con ese nombre.')
        
        # No permitir nombres de grupos del sistema (opcional)
        reserved_names = ['admin', 'staff', 'delivery']
        if name.lower() in reserved_names and self.original_name.lower() != name.lower():
            raise ValidationError(f'El nombre "{name}" está reservado para grupos del sistema.')
        
        return name


class GroupDeleteForm(FormStyleMixin, forms.Form):
    """
    Formulario para eliminar grupos/roles.
    """
    
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
            raise ValidationError('Rol no especificado.')
        
        if self.group.name.lower() != value:
            raise ValidationError('El nombre del rol no coincide.')
        
        # No permitir eliminar grupos del sistema
        protected_groups = ['admin', 'staff', 'delivery']
        if self.group.name.lower() in protected_groups:
            raise ValidationError(f'No se puede eliminar el rol "{self.group.name}" porque es un rol del sistema.')
        
        # Verificar si hay usuarios asignados
        user_count = self.group.user_set.count()
        if user_count > 0:
            raise ValidationError(
                f'No se puede eliminar este rol porque tiene {user_count} usuario(s) asignado(s). '
                f'Reasigna o elimina esos usuarios primero.'
            )
        
        return value


# ========== PROFILE FORMS (para que los usuarios editen su propio perfil) ==========

class UserProfileForm(FormStyleMixin, forms.ModelForm):
    """
    Formulario para que los usuarios editen su propio perfil.
    Campos limitados por seguridad.
    """
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(),
            'last_name': forms.TextInput(),
            'email': forms.EmailInput(),
            'phone': forms.TextInput(attrs={'placeholder': 'Ej: 3001234567'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No permitir cambiar username por seguridad
        if self.instance and self.instance.username:
            self.fields['email'].required = False
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        
        if phone:
            digits = ''.join(c for c in phone if c.isdigit())
            
            if len(digits) < 7:
                raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
            
            if len(digits) > 15:
                raise ValidationError('El teléfono no puede tener más de 15 dígitos.')
            
            # Verificar si otro usuario tiene el mismo teléfono
            qs = User.objects.filter(phone=digits)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Este número de teléfono ya está registrado por otro usuario.')
            
            return digits
        
        return phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if email:
            qs = User.objects.filter(email__iexact=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Este correo electrónico ya está registrado por otro usuario.')
        
        return email


class UserPasswordChangeForm(FormStyleMixin, forms.Form):
    """
    Formulario para que los usuarios cambien su propia contraseña.
    Requiere contraseña actual.
    """
    
    current_password = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(),
        required=True,
    )
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(),
        required=True,
        min_length=8,
    )
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(),
        required=True,
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password', '')
        
        if not self.user:
            raise ValidationError('Usuario no especificado.')
        
        if not self.user.check_password(current_password):
            raise ValidationError('La contraseña actual es incorrecta.')
        
        return current_password
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1', '')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        if password.isdigit():
            raise ValidationError('La contraseña no puede ser completamente numérica.')
        
        if password.lower() in ['password', '12345678', 'qwerty123']:
            raise ValidationError('La contraseña es demasiado común.')
        
        # Evitar contraseña igual a la actual
        if self.user and self.user.check_password(password):
            raise ValidationError('La nueva contraseña no puede ser igual a la actual.')
        
        return password
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        
        return password2
    
    def save(self):
        """
        Guarda la nueva contraseña.
        """
        password = self.cleaned_data.get('new_password1')
        self.user.set_password(password)
        self.user.save(update_fields=['password'])
        return self.user


# ========== DELIVERY USER FORMS (versiones simplificadas para PWA) ==========

class DeliveryUserProfileForm(FormStyleMixin, forms.ModelForm):
    """
    Formulario simplificado para que los repartidores actualicen su perfil.
    """
    
    class Meta:
        model = User
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': 'Ej: 3001234567'}),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = ''.join(c for c in phone if c.isdigit())
        
        if len(digits) < 7:
            raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
        
        if len(digits) > 15:
            raise ValidationError('El teléfono no puede tener más de 15 dígitos.')
        
        return digits