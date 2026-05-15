from django.contrib import admin

from organizacion.models import ComiteGrupoCargo, ConsejoGrupo, GrupoScout, InstitucionPatrocinante
from unidades.models import Unidad


class InstitucionPatrocinanteInline(admin.TabularInline):
    model = InstitucionPatrocinante
    extra = 0


class ComiteGrupoCargoInline(admin.TabularInline):
    model = ComiteGrupoCargo
    extra = 0
    autocomplete_fields = ("apoderado",)


class UnidadInline(admin.TabularInline):
    model = Unidad
    extra = 0
    autocomplete_fields = ("rama",)
    fields = ("nombre", "rama", "tipo_composicion", "estado", "cupo_maximo")


@admin.action(description="Recalcular minimo de miembros")
def recalcular_minimo(modeladmin, request, queryset):
    for grupo in queryset:
        grupo.recalcular_minimo_miembros(save=True)


@admin.register(GrupoScout)
class GrupoScoutAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_oficial",
        "zona",
        "distrito",
        "logo",
        "estado_vigencia",
        "minimo_miembros_calculado",
    )
    list_filter = ("estado_vigencia", "tipo_grupo", "zona", "distrito")
    search_fields = ("nombre_oficial", "comuna")
    autocomplete_fields = ("zona", "distrito")
    readonly_fields = ("minimo_miembros_calculado",)
    actions = [recalcular_minimo]
    inlines = [InstitucionPatrocinanteInline, ComiteGrupoCargoInline, UnidadInline]


@admin.register(ConsejoGrupo)
class ConsejoGrupoAdmin(admin.ModelAdmin):
    list_display = ("grupo", "responsable_grupo")
    autocomplete_fields = ("grupo", "responsable_grupo")


@admin.register(InstitucionPatrocinante)
class InstitucionPatrocinanteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "grupo", "logo", "fecha_inicio_convenio", "fecha_fin_convenio")
    list_filter = ("tipo",)
    search_fields = ("nombre", "grupo__nombre_oficial", "logo")
    autocomplete_fields = ("grupo",)


@admin.register(ComiteGrupoCargo)
class ComiteGrupoCargoAdmin(admin.ModelAdmin):
    list_display = ("grupo", "rol", "apoderado")
    list_filter = ("rol",)
    autocomplete_fields = ("grupo", "apoderado")

# Register your models here.
