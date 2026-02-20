from django import forms
from .models import Report, Section


class ReportForm(forms.ModelForm):
    report_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': '.pdf,.doc,.docx'
        }),
        label='Текст доклада',
        help_text='Текст доклада в формате DOC, DOCX или PDF'
    )

    presentation_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': '.pdf,.ppt,.pptx'
        }),
        label='Презентация (опционально)',
        help_text='Презентация в формате PPT, PPTX или PDF'
    )

    # НОВОЕ ПОЛЕ: Архив с фото/видео
    media_archive = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': '.zip,.rar,.7z'
        }),
        label='Архив с фото/видео (опционально)',
        help_text='ZIP или RAR архив с фотографиями и видео (макс. 50MB)'
    )

    abstract = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'input-field',
            'rows': 4,
            'placeholder': 'Краткое описание доклада (200-500 слов)'
        }),
        label='Аннотация доклада',
        help_text='Краткое описание содержания доклада'
    )

    class Meta:
        model = Report
        fields = ['title', 'abstract', 'section', 'report_file', 'presentation_file', 'media_archive']

    def clean_report_file(self):
        file = self.cleaned_data.get('report_file')
        if file:
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Файл слишком большой. Максимальный размер: 10MB')

            allowed_extensions = ['.pdf', '.doc', '.docx']
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError('Неподдерживаемый формат файла. Используйте PDF, DOC или DOCX.')

        return file

    def clean_presentation_file(self):
        file = self.cleaned_data.get('presentation_file')
        if file:
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Файл презентации слишком большой. Максимальный размер: 10MB')

            allowed_extensions = ['.pdf', '.ppt', '.pptx']
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError('Неподдерживаемый формат файла. Используйте PDF, PPT или PPTX.')

        return file

    def clean_media_archive(self):
        """Валидация архива с фото/видео"""
        file = self.cleaned_data.get('media_archive')
        if file:
            if file.size > 50 * 1024 * 1024:  # 50MB
                raise forms.ValidationError('Архив слишком большой. Максимальный размер: 50MB')

            allowed_extensions = ['.zip', '.rar', '.7z']
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError('Неподдерживаемый формат архива. Используйте ZIP, RAR или 7Z.')

        return file


class ReportResubmitForm(forms.ModelForm):
    """Форма для повторной отправки доклада после доработок"""

    revision_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'input-field',
            'rows': 6,
            'placeholder': 'Опишите, какие изменения вы внесли в доклад на основе замечаний...'
        }),
        label='Описание внесенных изменений',
        required=True,
        help_text='Подробно опишите, какие именно исправления и доработки были выполнены'
    )

    report_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': '.pdf,.doc,.docx'
        }),
        label='Обновленный текст доклада',
        help_text='Загрузите исправленную версию доклада (если файл был изменен)'
    )

    presentation_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': '.pdf,.ppt,.pptx'
        }),
        label='Обновленная презентация (опционально)',
        help_text='Загрузите исправленную версию презентации (если файл был изменен)'
    )

    # НОВОЕ ПОЛЕ для повторной отправки
    media_archive = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': '.zip,.rar,.7z'
        }),
        label='Обновленный архив с фото/видео (опционально)',
        help_text='Загрузите исправленную версию архива (если файл был изменен)'
    )

    class Meta:
        model = Report
        fields = ['title', 'abstract', 'keywords', 'report_file', 'presentation_file', 'media_archive', 'revision_description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Название доклада'
            }),
            'abstract': forms.Textarea(attrs={
                'class': 'input-field',
                'rows': 8,
                'placeholder': 'Аннотация доклада...'
            }),
            'keywords': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Ключевые слова через запятую'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поля необязательными при повторной отправке
        self.fields['report_file'].required = False
        self.fields['media_archive'].required = False
        self.fields['revision_description'].required = True

        # Если есть существующий файл, показываем подсказку
        if self.instance and self.instance.pk:
            if self.instance.report_file:
                self.fields['report_file'].help_text = f'Текущий файл: {self.instance.report_file.name}. Оставьте пустым, чтобы сохранить текущий файл.'
            if self.instance.presentation_file:
                self.fields['presentation_file'].help_text = f'Текущий файл: {self.instance.presentation_file.name}. Оставьте пустым, чтобы сохранить текущий файл.'
            if self.instance.media_archive:
                self.fields['media_archive'].help_text = f'Текущий архив: {self.instance.media_archive.name}. Оставьте пустым, чтобы сохранить текущий архив.'

    def clean(self):
        cleaned_data = super().clean()
        report_file = cleaned_data.get('report_file')

        # Проверяем, что либо загружен новый файл, либо есть существующий
        if not report_file and self.instance and not self.instance.report_file:
            raise forms.ValidationError('Необходимо загрузить файл доклада.')

        return cleaned_data
