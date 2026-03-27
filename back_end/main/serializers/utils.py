from rest_framework import serializers

class SimpleStringSerializer(serializers.Serializer):
    name = serializers.CharField()