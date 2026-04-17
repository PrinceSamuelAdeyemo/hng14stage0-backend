from rest_framework import serializers
from .models import Profile
from django.utils import timezone

class ProfileSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = [
            'id', 'name', 'gender', 'gender_probability', 'sample_size',
            'age', 'age_group', 'country_id', 'country_probability', 'created_at'
        ]
    
    def get_created_at(self, obj):
        """Format created_at as UTC ISO 8601 with Z suffix"""
        if obj.created_at:
            # Ensure it's in UTC and format with Z suffix
            return obj.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        return None
