from django.shortcuts import render, get_object_or_404
from django.http import FileResponse
from .models import Document

def conference_info(request):
    documents = Document.objects.all()  # Все документы
    print(f"Найдено документов: {documents.count()}")  # Для отладки
    return render(request, 'docs/info.html', {'documents': documents})

def download_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    filename = doc.file.name.split('/')[-1]
    return FileResponse(
        doc.file.open('rb'),
        as_attachment=True,
        filename=filename
    )
