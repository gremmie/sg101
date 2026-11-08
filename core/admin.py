from django.contrib import admin


class PlainTextFieldsMixin:
    """
    Keeps TinyMCE off the textareas named in `plain_text_fields`.

    TinyMCE's init skips any textarea with the class mceNoEditor. The class has
    to be in the served HTML: TinyMCE converts textareas as soon as the document
    is parsed, before any jQuery ready handler could add it.

    """
    plain_text_fields = []

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in self.plain_text_fields:
            classes = formfield.widget.attrs.get('class', '')
            formfield.widget.attrs['class'] = (classes + ' mceNoEditor').strip()
        return formfield

