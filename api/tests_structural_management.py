from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from catalogos.models import ComposicionPermitida, Distrito, Rama, Zona
from organizacion.models import ConsejoGrupo, GrupoScout, TipoGrupo
from personas.models import Adulto, Beneficiario, Persona, RolAdulto, SexoPersona
from unidades.models import AdultoUnidadRol, RolAdultoUnidad, Subgrupo, SubgrupoMiembro, Unidad
from unidades.selectors import duplicate_adult_unit_role_pairs
from unidades.services import (
    create_adulto_unidad_rol, create_subgrupo_miembro, reassign_subgrupo_miembro,
    update_adulto_unidad_rol, update_unidad,
)
from api.v1.personas.services import reassign_beneficiario


class StructuralFixtureMixin:
    def make_persona(self, rut, sexo, nombre="Persona"):
        return Persona.objects.create(
            rut=rut, nombres=nombre, apellidos="Prueba", fecha_nacimiento="1990-01-01",
            sexo=sexo, direccion="Direccion", telefono="123", email=f"{rut}@example.test",
        )

    def make_beneficiario(self, rut, sexo, unidad, nombre="Beneficiario"):
        return Beneficiario.objects.create(
            persona=self.make_persona(rut, sexo, nombre), rama_actual=unidad.rama,
            unidad=unidad, fecha_ingreso="2025-01-01",
        )

    def make_adulto(self, rut, sexo):
        return Adulto.objects.create(
            persona=self.make_persona(rut, sexo, "Adulto"), rol_principal=RolAdulto.GUIA,
            certificado_inhabilidades="certificados/test.pdf",
            certificado_vigencia_hasta=timezone.localdate() + timezone.timedelta(days=30),
        )


class StructuralServiceTests(StructuralFixtureMixin, TestCase):
    def setUp(self):
        zona = Zona.objects.create(nombre="Zona estructural")
        distrito = Distrito.objects.create(nombre="Distrito estructural", zona=zona)
        self.rama = Rama.objects.create(nombre="Rama estructural", edad_minima=7, edad_maxima=18, nomenclatura_subgrupos="Equipos")
        self.grupo = GrupoScout.objects.create(nombre_oficial="Grupo estructural", zona=zona, distrito=distrito, tipo_grupo=TipoGrupo.PLURICONFESIONAL, direccion="Direccion", comuna="Comuna")
        self.unidad = Unidad.objects.create(grupo=self.grupo, rama=self.rama, nombre="Unidad origen", cupo_maximo=2)
        self.destino = Unidad.objects.create(grupo=self.grupo, rama=self.rama, nombre="Unidad destino", cupo_maximo=2)
        self.user = get_user_model().objects.create_user(username="auditor")

    def test_cupo_y_composicion_no_admiten_poblacion_existente_incompatible(self):
        self.make_beneficiario("11111111-1", SexoPersona.FEMENINO, self.unidad)
        self.make_beneficiario("22222222-2", SexoPersona.FEMENINO, self.unidad)
        tercero = Beneficiario(persona=self.make_persona("33333333-3", SexoPersona.FEMENINO), rama_actual=self.rama, unidad=self.unidad, fecha_ingreso="2025-01-01")
        with self.assertRaises(ValidationError):
            tercero.full_clean()
        with self.assertRaises(ValidationError):
            update_unidad(user=self.user, unidad=self.unidad, data={"cupo_maximo": 1})
        with self.assertRaises(ValidationError):
            update_unidad(user=self.user, unidad=self.unidad, data={"tipo_composicion": ComposicionPermitida.SOLO_HOMBRES})

    def test_role_is_unique_and_sole_responsible_cannot_be_demoted(self):
        adulto = self.make_adulto("44444444-4", SexoPersona.MASCULINO)
        asignacion = AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto, rol=RolAdultoUnidad.RESPONSABLE)
        duplicate = AdultoUnidadRol(unidad=self.unidad, adulto=adulto, rol=RolAdultoUnidad.ASISTENTE)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        with self.assertRaises(ValidationError):
            update_adulto_unidad_rol(user=self.user, asignacion=asignacion, data={"rol": RolAdultoUnidad.ASISTENTE})

    def test_role_integrity_errors_are_normalized(self):
        adulto = self.make_adulto("16161616-1", SexoPersona.MASCULINO)
        with patch("unidades.services._save", side_effect=IntegrityError):
            with self.assertRaises(ValidationError) as create_error:
                create_adulto_unidad_rol(
                    user=self.user,
                    data={"unidad": self.unidad, "adulto": adulto, "rol": RolAdultoUnidad.ASISTENTE},
                )
        self.assertIn("rol", create_error.exception.message_dict)

        asignacion = AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=adulto, rol=RolAdultoUnidad.ASISTENTE)
        with patch("unidades.services._save", side_effect=IntegrityError):
            with self.assertRaises(ValidationError) as update_error:
                update_adulto_unidad_rol(user=self.user, asignacion=asignacion, data={"rol": RolAdultoUnidad.RESPONSABLE})
        self.assertIn("rol", update_error.exception.message_dict)

    def test_duplicate_role_report_is_empty_for_valid_data(self):
        self.assertEqual(list(duplicate_adult_unit_role_pairs()), [])
        call_command("verificar_roles_adulto_unidad")

    def test_nullable_unit_joins_lock_only_beneficiario_on_postgresql(self):
        if connection.vendor != "postgresql":
            self.skipTest("La clausula OF se valida en PostgreSQL.")
        beneficiario = self.make_beneficiario("17171717-1", SexoPersona.MASCULINO, self.unidad)
        origen = Subgrupo.objects.create(nombre="Bloqueo origen", unidad=self.unidad)
        with CaptureQueriesContext(connection) as queries:
            create_subgrupo_miembro(user=self.user, data={"subgrupo": origen, "beneficiario": beneficiario})
        self.assertTrue(any('FOR UPDATE OF "personas_beneficiario"' in query["sql"] for query in queries.captured_queries))

    def test_beneficiario_reassignment_uses_base_table_lock_on_postgresql(self):
        if connection.vendor != "postgresql":
            self.skipTest("La clausula OF se valida en PostgreSQL.")
        beneficiario = self.make_beneficiario("18181818-1", SexoPersona.MASCULINO, self.unidad)
        with CaptureQueriesContext(connection) as queries:
            reassign_beneficiario(
                user=self.user,
                beneficiario=beneficiario,
                data={"unidad": self.destino, "rama_actual": self.rama},
            )
        self.assertTrue(any('FOR UPDATE OF "personas_beneficiario"' in query["sql"] for query in queries.captured_queries))

    def test_leader_must_be_member_and_reassignment_updates_history(self):
        beneficiario = self.make_beneficiario("55555555-5", SexoPersona.MASCULINO, self.unidad)
        origen = Subgrupo.objects.create(nombre="Origen", unidad=self.unidad)
        destino = Subgrupo.objects.create(nombre="Destino", unidad=self.destino)
        origen.lider_juvenil = beneficiario
        with self.assertRaises(ValidationError):
            origen.full_clean()
        miembro = SubgrupoMiembro.objects.create(subgrupo=origen, beneficiario=beneficiario)
        resultado = reassign_subgrupo_miembro(user=self.user, miembro=miembro, subgrupo=destino)
        resultado.refresh_from_db()
        beneficiario.refresh_from_db()
        self.assertEqual(resultado.subgrupo_id, destino.id)
        self.assertEqual(beneficiario.unidad_id, self.destino.id)
        self.assertEqual(resultado.history.first().history_user, self.user)
        self.assertEqual(beneficiario.history.first().history_user, self.user)


class StructuralApiTests(StructuralFixtureMixin, APITestCase):
    def setUp(self):
        zona = Zona.objects.create(nombre="Zona API estructural")
        distrito = Distrito.objects.create(nombre="Distrito API estructural", zona=zona)
        rama = Rama.objects.create(nombre="Rama API estructural", edad_minima=7, edad_maxima=18, nomenclatura_subgrupos="Equipos")
        grupo = GrupoScout.objects.create(nombre_oficial="Grupo API estructural", zona=zona, distrito=distrito, tipo_grupo=TipoGrupo.PLURICONFESIONAL, direccion="Direccion", comuna="Comuna")
        self.unidad = Unidad.objects.create(grupo=grupo, rama=rama, nombre="Unidad API")
        self.subgrupo = Subgrupo.objects.create(nombre="Equipo API", unidad=self.unidad)
        self.miembro = SubgrupoMiembro.objects.create(subgrupo=self.subgrupo, beneficiario=self.make_beneficiario("66666666-6", SexoPersona.MASCULINO, self.unidad))
        self.user = get_user_model().objects.create_user(username="staff", is_staff=True)
        self.client.force_authenticate(self.user)

    def test_generic_membership_write_and_delete_are_not_exposed(self):
        detail = reverse("v1:subgrupos-miembros-detail", args=[self.miembro.id])
        self.assertEqual(self.client.patch(detail, {"subgrupo": self.subgrupo.id}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_reassignment_accepts_only_destination_subgroup(self):
        url = reverse("v1:subgrupos-miembros-reasignacion", args=[self.miembro.id])
        response = self.client.patch(url, {"subgrupo": self.subgrupo.id, "beneficiario": self.miembro.beneficiario_id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])


class StructuralAuthorizationTests(StructuralFixtureMixin, APITestCase):
    def setUp(self):
        zona = Zona.objects.create(nombre="Zona permisos")
        distrito = Distrito.objects.create(nombre="Distrito permisos", zona=zona)
        rama = Rama.objects.create(nombre="Rama permisos", edad_minima=7, edad_maxima=18, nomenclatura_subgrupos="Equipos")
        self.grupo = GrupoScout.objects.create(nombre_oficial="Grupo permisos", zona=zona, distrito=distrito, tipo_grupo=TipoGrupo.PLURICONFESIONAL, direccion="Direccion", comuna="Comuna")
        self.unidad = Unidad.objects.create(grupo=self.grupo, rama=rama, nombre="Unidad permisos")
        self.destino_unidad = Unidad.objects.create(grupo=self.grupo, rama=rama, nombre="Unidad destino permisos")
        self.subgrupo = Subgrupo.objects.create(nombre="Equipo permisos", unidad=self.unidad)
        self.destino = Subgrupo.objects.create(nombre="Equipo destino permisos", unidad=self.destino_unidad)
        self.miembro = SubgrupoMiembro.objects.create(subgrupo=self.subgrupo, beneficiario=self.make_beneficiario("77777777-7", SexoPersona.MASCULINO, self.unidad))
        self.disponible = self.make_beneficiario("88888888-8", SexoPersona.MASCULINO, self.unidad)
        self.disponible_colaborador = self.make_beneficiario("15151515-1", SexoPersona.MASCULINO, self.unidad)

        self.manager = self._user_with_adult("manager", "99999999-9")
        ConsejoGrupo.objects.create(grupo=self.grupo, responsable_grupo=self.manager.persona.adulto)
        self.asistente = self._user_with_adult("asistente", "10101010-1")
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=self.asistente.persona.adulto, rol=RolAdultoUnidad.ASISTENTE)
        AdultoUnidadRol.objects.create(unidad=self.destino_unidad, adulto=self.asistente.persona.adulto, rol=RolAdultoUnidad.ASISTENTE)
        self.colaborador = self._user_with_adult("colaborador", "12121212-1")
        AdultoUnidadRol.objects.create(unidad=self.unidad, adulto=self.colaborador.persona.adulto, rol=RolAdultoUnidad.COLABORADOR)
        self.prelinked = self.make_adulto("13131313-1", SexoPersona.MASCULINO)
        AdultoUnidadRol.objects.create(unidad=self.destino_unidad, adulto=self.prelinked, rol=RolAdultoUnidad.COLABORADOR)
        self.unlinked = self.make_adulto("14141414-1", SexoPersona.MASCULINO)

    def _user_with_adult(self, username, rut):
        user = get_user_model().objects.create_user(username=username)
        adulto = self.make_adulto(rut, SexoPersona.MASCULINO)
        adulto.persona.usuario = user
        adulto.persona.save(update_fields=["usuario"])
        return user

    def _auth(self, user):
        self.client.force_authenticate(user)

    def test_structural_writes_separate_group_and_membership_permissions(self):
        self._auth(self.asistente)
        self.assertEqual(self.client.patch(reverse("v1:unidades-detail", args=[self.unidad.id]), {"nombre": "No"}, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(reverse("v1:subgrupos-list"), {"nombre": "No", "unidad": self.unidad.id}, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(reverse("v1:unidades-adultos-roles-list"), {"unidad": self.unidad.id, "adulto": self.prelinked.id, "rol": RolAdultoUnidad.COLABORADOR}, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.post(reverse("v1:subgrupos-miembros-list"), {"subgrupo": self.subgrupo.id, "beneficiario": self.disponible.id}, format="json").status_code, status.HTTP_201_CREATED)

        self._auth(self.colaborador)
        self.assertEqual(self.client.post(reverse("v1:subgrupos-miembros-list"), {"subgrupo": self.subgrupo.id, "beneficiario": self.disponible_colaborador.id}, format="json").status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_capabilities_and_option_scopes_are_exact(self):
        self._auth(self.asistente)
        unit = self.client.get(reverse("v1:unidades-detail", args=[self.unidad.id]))
        self.assertEqual(unit.data["meta"]["permissions"], {"can_edit": False, "can_create_subgroup": False, "can_manage_memberships": True, "can_manage_adult_assignments": False})
        self.assertEqual(self.client.get(reverse("v1:unidades-opciones-grupos")).data["data"], [])
        membership_options = self.client.get(reverse("v1:unidades-opciones-beneficiarios"), {"unidad_id": self.unidad.id})
        self.assertEqual({item["id"] for item in membership_options.data["data"]}, {self.disponible.id, self.disponible_colaborador.id})
        self.assertEqual(self.client.get(reverse("v1:unidades-opciones-adultos"), {"unidad_id": self.unidad.id}).status_code, status.HTTP_403_FORBIDDEN)

        self._auth(self.manager)
        leader_options = self.client.get(reverse("v1:unidades-opciones-beneficiarios"), {"subgrupo_id": self.subgrupo.id})
        self.assertEqual({item["id"] for item in leader_options.data["data"]}, {self.miembro.beneficiario_id})
        adult_options = self.client.get(reverse("v1:unidades-opciones-adultos"), {"unidad_id": self.unidad.id})
        adult_ids = {item["id"] for item in adult_options.data["data"]}
        self.assertIn(self.prelinked.id, adult_ids)
        self.assertNotIn(self.unlinked.id, adult_ids)
        destinations = self.client.get(reverse("v1:unidades-opciones-destinos-membresia"), {"miembro_id": self.miembro.id})
        self.assertTrue(destinations.data["data"])
        self.assertEqual(set(destinations.data["data"][0]), {"id", "nombre", "unidad", "unidad_nombre"})
