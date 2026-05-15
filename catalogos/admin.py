from django.contrib import admin

from catalogos.models import Distrito, Rama, Zona


@admin.register(Distrito)
class DistritoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "zona")
    list_filter = ("zona",)
    search_fields = ("nombre", "zona__nombre")
    autocomplete_fields = ("zona",)


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Rama)
class RamaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edad_minima", "edad_maxima", "composicion_permitida", "activa")
    list_filter = ("composicion_permitida", "activa")
    search_fields = ("nombre",)
