from django.contrib import admin

from unidades.models import AdultoUnidadRol, Subgrupo, SubgrupoMiembro, Unidad


class SubgrupoInline(admin.TabularInline):
    model = Subgrupo
    extra = 0
    autocomplete_fields = ("lider_juvenil",)


class AdultoUnidadRolInline(admin.TabularInline):
    model = AdultoUnidadRol
    extra = 0
    autocomplete_fields = ("adulto",)


@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "grupo", "rama", "estado", "cupo_maximo")
    list_filter = ("estado", "rama")
    search_fields = ("nombre", "grupo__nombre_oficial")
    autocomplete_fields = ("grupo", "rama")
    inlines = [SubgrupoInline, AdultoUnidadRolInline]


@admin.register(Subgrupo)
class SubgrupoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "unidad", "lider_juvenil")
    search_fields = ("nombre", "unidad__nombre")
    autocomplete_fields = ("unidad", "lider_juvenil")


@admin.register(SubgrupoMiembro)
class SubgrupoMiembroAdmin(admin.ModelAdmin):
    list_display = ("subgrupo", "beneficiario")
    autocomplete_fields = ("subgrupo", "beneficiario")


@admin.register(AdultoUnidadRol)
class AdultoUnidadRolAdmin(admin.ModelAdmin):
    list_display = ("unidad", "adulto", "rol")
    list_filter = ("rol",)
    autocomplete_fields = ("unidad", "adulto")

# Register your models here.
