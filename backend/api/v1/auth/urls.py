from django.urls import path

from api.v1.auth.views import LogoutView, MeView, ScoutTokenObtainPairView, ScoutTokenRefreshView

urlpatterns = [
    path("token/", ScoutTokenObtainPairView.as_view(), name="auth-token"),
    path("token/refresh/", ScoutTokenRefreshView.as_view(), name="auth-token-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
]
