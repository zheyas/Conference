from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file', 'uploaded_at']
    search_fields = ['title']
    list_filter = ['uploaded_at']