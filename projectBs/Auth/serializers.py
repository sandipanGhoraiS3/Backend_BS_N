from rest_framework import serializers
from .models import BSUser
# from django.conf import settings
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class BSUserSerializer(serializers.ModelSerializer):
    # id = serializers.IntegerField(source='_id', read_only=True)  # Expose '_id' as 'id'

    class Meta:
        model = BSUser
        fields = ('_id', 'username', 'first_name', 'last_name', 'phone_number', 'password',
                  'is_superuser', 'date_joined', 'updated_at', 'last_login_at', 'is_active')

        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def create(self, validated_data):
        user = BSUser.objects.create_user(**validated_data)
        return user
