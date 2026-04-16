from django.urls import path
from .views import ProfileListCreateView, ProfileDetailView

urlpatterns = [
    path('api/profiles', ProfileListCreateView.as_view()),
    path('api/profiles/', ProfileListCreateView.as_view()),
    path('api/profiles/<uuid:pk>', ProfileDetailView.as_view()),
    path('api/profiles/<uuid:pk>/', ProfileDetailView.as_view()),
]
