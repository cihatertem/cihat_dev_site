from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import datetime, timedelta

User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super(MyTokenObtainPairSerializer, self).validate(attrs)
        user = User.objects.get(username=attrs["username"])
        data["username"] = user.username
        data["user_email"] = user.email
        data["created_at"] = datetime.now()
        data["expired_at"] = datetime.now() + timedelta(days=30)
        return data
