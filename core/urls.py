from django.urls import path
from .views import ProfileListCreateView, ProfileDetailView, health_check

urlpatterns = [
    path('api/health', health_check, name='health_check'),
    path('api/profiles', ProfileListCreateView.as_view()),
    path('api/profiles/', ProfileListCreateView.as_view()),
    path('api/profiles/<uuid:pk>', ProfileDetailView.as_view()),
    path('api/profiles/<uuid:pk>/', ProfileDetailView.as_view()),
]
