from django.urls import path

from api.v1.dashboard.views import GrupoDashboardView

urlpatterns = [
    path("grupo/<int:pk>/", GrupoDashboardView.as_view(), name="dashboard-grupo"),
]
