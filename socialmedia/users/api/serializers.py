from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import re

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "name", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "username"}
        }


class UserCreateSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(label="Confirm Password", required=True, allow_null=False)

    class Meta:
        model = User
        fields = ["username", "name", "password", "password2"]

    def validate(self, data):
        if 'password' in data:
            if not 'password2' in data:
                raise ValidationError({"password2":("This field cannot be empty")})
            if not data['password'] == data['password2']:
                raise ValidationError({"password2":("Password fields don't match")})
            if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\da-zA-Z]).{8,15}$',data['password']):
                raise ValidationError({"password":("Password must contain 8-15 characters, an upper case character and a special character.")})
        if 'password2' in data and not 'password' in data:
            raise ValidationError({"password":("This field cannot be empty")})
        return data

    def save(self, validated_data):
        username = validated_data.pop('username')
        name = validated_data.pop('name')
        password = validated_data.pop('password')

        instance = User.objects.create(
            username=username,
            name=name,
            password=make_password(password),
        )
        return instance


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name"]

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance


#--------------------------------------------------------------------------------------------------------------


