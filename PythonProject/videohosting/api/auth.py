from ninja.security import HttpBearer
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import HttpRequest

class JWTAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str):
        validated = JWTAuthentication().authenticate(request)
        if validated is not None:
            # сбрасываем user вручную
            request.user = validated[0]
            return validated[0]
        # сбрасываем на AnonymousUser, если токен невалиден
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()
        return None
