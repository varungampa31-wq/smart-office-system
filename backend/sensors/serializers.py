from rest_framework import serializers
from .models import SensorEvent


class SensorEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorEvent
        fields = "__all__"