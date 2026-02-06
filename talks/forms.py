from django import forms
from .models import Report, Section


class ReportForm(forms.ModelForm):
    # Уберите section из явного определения, если оно уже есть в модели
    # section будет автоматически подхвачен из Meta.fields

    # Измените content_file на report_file (или оба поля, если нужно)
    report_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': '.pdf,.doc,.docx'
        }),
        label='Текст доклада',
        help_text='Текст доклада в формате DOC, DOCX или PDF'
    )

    # Опционально: добавьте поле для презентации
    presentation_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': '.pdf,.ppt,.pptx'
        }),
        label='Презентация (опционально)',
        help_text='Презентация в формате PPT, PPTX или PDF'
    )

    # Добавьте поле abstract, если его нет в форме
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
        fields = ['title', 'abstract', 'section', 'report_file', 'presentation_file']
        # Или fields = '__all__', но тогда будут все поля модели

    def clean_report_file(self):
        file = self.cleaned_data.get('report_file')
        if file:
            # Проверка размера файла (максимум 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Файл слишком большой. Максимальный размер: 10MB')

            # Проверка расширения
            allowed_extensions = ['.pdf', '.doc', '.docx']
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError('Неподдерживаемый формат файла. Используйте PDF, DOC или DOCX.')

        return file

    def clean_presentation_file(self):
        file = self.cleaned_data.get('presentation_file')
        if file:
            # Проверка размера файла (максимум 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Файл презентации слишком большой. Максимальный размер: 10MB')

            # Проверка расширения
            allowed_extensions = ['.pdf', '.ppt', '.pptx']
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError('Неподдерживаемый формат файла. Используйте PDF, PPT или PPTX.')

        return file
