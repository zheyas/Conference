from django import forms
from django.core.exceptions import ValidationError
from .models import Document


class DocumentForm(forms.ModelForm):
    """Простая форма для документов"""

    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название документа'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверка размера файла (макс 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('Файл слишком большой. Максимальный размер: 10MB')

            # Проверка расширения файла
            allowed_extensions = ['.doc', '.docx', '.pdf']
            ext = file.name.lower()
            if not any(ext.endswith(e) for e in allowed_extensions):
                raise ValidationError('Неподдерживаемый формат файла. Используйте DOC, DOCX или PDF.')

        return file
