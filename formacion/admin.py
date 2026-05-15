from django.contrib import admin

from formacion.models import AdultoGradoFormacion, GradoFormacion


@admin.register(GradoFormacion)
class GradoFormacionAdmin(admin.ModelAdmin):
    list_display = ("nivel", "especialidad")
    list_filter = ("nivel",)
    search_fields = ("nivel", "especialidad")


@admin.register(AdultoGradoFormacion)
class AdultoGradoFormacionAdmin(admin.ModelAdmin):
    list_display = ("adulto", "grado", "fecha_obtencion")
    list_filter = ("grado__nivel",)
    autocomplete_fields = ("adulto", "grado")

# Register your models here.
