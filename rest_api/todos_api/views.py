from rest_framework import viewsets
from rest_framework import permissions
from todos_api.models import Todo
from .serializers import TodoSerializer
import jwt
from core.settings import SECRET_KEY


class ToDoUserCustomPermission(permissions.BasePermission):
    message = "Forbidden."

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class TodoListViewSet(viewsets.ModelViewSet, ToDoUserCustomPermission):
    def get_user_id(self):
        token = self.request.headers["Authorization"].split(" ")[1]
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]

    def get_queryset(self, *args, **kwargs):
        if self.request.user.is_superuser:
            return Todo.objects.all()
        return Todo.objects.all().filter(user=self.request.user)

    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    permission_classes = [permissions.IsAuthenticated, ToDoUserCustomPermission]
