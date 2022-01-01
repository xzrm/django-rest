from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import permissions
from todos_api.models import Todo
from users.models import NewUser
from .serializers import TodoSerializer
import jwt
from core.settings import SECRET_KEY
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.http import Http404
from rest_framework.exceptions import PermissionDenied


class ToDoUserCustomPermission(permissions.BasePermission):
    message = "Forbidden."

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.user == request.user


class TodoListViewSet(viewsets.ModelViewSet, ToDoUserCustomPermission):
    def get_user_id(self):
        token = self.request.headers["Authorization"].split(" ")[1]
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]

    def get_user_obj(self, id):
        try:
            return NewUser.objects.get(id=id)
        except NewUser.DoesNotExist:
            raise Http404

    def create(self, request):
        user_id = self.get_user_id()
        user = self.get_user_obj(user_id)
        serializer = TodoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data)

    def update(self, request, pk):
        todo = Todo.objects.get(pk=pk)
        user_id = self.get_user_id()
        user = self.get_user_obj(user_id)

        def update_user_field_if_authorized():
            if "user" in request.data:
                if todo.user.id != request.data["user"]:
                    if not user.is_superuser:
                        raise PermissionDenied
                    else:
                        return self.get_user_obj(request.data["user"])
            return None

        serializer = TodoSerializer(todo, data=request.data)
        if serializer.is_valid():
            updated_user = update_user_field_if_authorized()
            if updated_user:
                serializer.save(user=updated_user)
            else:
                serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self, *args, **kwargs):
        if self.request.user.is_superuser:
            return Todo.objects.all()
        return Todo.objects.all().filter(user=self.request.user)

    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    permission_classes = [permissions.IsAuthenticated, ToDoUserCustomPermission]
