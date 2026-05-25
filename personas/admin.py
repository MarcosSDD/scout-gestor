from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from personas.models import Adulto, Apoderado, ApoderadoBeneficiario, Beneficiario, Persona


class ApoderadoBeneficiarioInline(admin.TabularInline):
    model = ApoderadoBeneficiario
    fk_name = "beneficiario"
    extra = 0
    autocomplete_fields = ("apoderado",)


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ("rut", "nombres", "apellidos", "estado", "telefono")
    list_filter = ("estado", "sexo")
    search_fields = ("rut", "nombres", "apellidos", "email")
    readonly_fields = ("foto_preview",)

    def foto_preview(self, obj):
        if not obj.foto:
            return "Sin foto"
        return format_html('<img src="{}" style="max-height: 120px; max-width: 120px;" />', obj.foto.url)

    foto_preview.short_description = "Vista previa de foto"


@admin.register(Adulto)
class AdultoAdmin(admin.ModelAdmin):
    list_display = ("persona", "rol_principal", "certificado_vigencia_hasta", "certificado_vigente")
    list_filter = ("rol_principal",)
    search_fields = ("persona__nombres", "persona__apellidos", "persona__rut")
    autocomplete_fields = ("persona",)
    actions = ["validar_certificados"]

    @admin.action(description="Validar vigencia de certificados")
    def validar_certificados(self, request, queryset):
        vigentes = sum(1 for adulto in queryset if adulto.certificado_vigente)
        vencidos = queryset.count() - vigentes
        self.message_user(
            request,
            f"Certificados vigentes: {vigentes} | vencidos: {vencidos}",
            level=messages.INFO,
        )


@admin.register(Apoderado)
class ApoderadoAdmin(admin.ModelAdmin):
    list_display = ("persona", "es_miembro_comite", "rol_comite")
    list_filter = ("es_miembro_comite",)
    search_fields = ("persona__nombres", "persona__apellidos", "persona__rut")
    autocomplete_fields = ("persona",)


@admin.register(Beneficiario)
class BeneficiarioAdmin(admin.ModelAdmin):
    list_display = ("persona", "rama_actual", "unidad", "fecha_ingreso")
    list_filter = ("rama_actual",)
    search_fields = ("persona__nombres", "persona__apellidos", "persona__rut")
    autocomplete_fields = ("persona", "rama_actual", "unidad")
    inlines = [ApoderadoBeneficiarioInline]


@admin.register(ApoderadoBeneficiario)
class ApoderadoBeneficiarioAdmin(admin.ModelAdmin):
    list_display = ("apoderado", "beneficiario", "parentesco", "autoriza_salidas_terreno")
    list_filter = ("parentesco", "autoriza_salidas_terreno")
    autocomplete_fields = ("apoderado", "beneficiario")

# Register your models here.
