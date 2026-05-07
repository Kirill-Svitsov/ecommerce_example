from rest_framework import generics, permissions
from rest_framework import viewsets
from django_filters import rest_framework as filters

from .models import Contact, Feedback
from .serializers import ContactSerializer, ContactUpdateSerializer, FeedbackSerializer


class FeedbackFilter(filters.FilterSet):
    email = filters.CharFilter(field_name="email", lookup_expr="icontains")
    user_first_name = filters.CharFilter(field_name="user_id__first_name", lookup_expr="icontains")
    user_last_name = filters.CharFilter(field_name="user_id__last_name", lookup_expr="icontains")

    class Meta:
        model = Feedback
        fields = ["email", "user_first_name", "user_last_name"]


class ContactDetailView(generics.RetrieveAPIView):
    """Получить контакты (доступно всем)"""

    serializer_class = ContactSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return Contact.objects.first()


class ContactUpdateView(generics.UpdateAPIView):
    """Обновить контакты (только админ)"""

    serializer_class = ContactUpdateSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_object(self):
        contact = Contact.objects.first()
        if not contact:
            contact = Contact.objects.create(
                phone_1="+7 (999) 123-45-67",
                email="info@tocco.ru",
                address_ru="г. Москва, ул. Примерная, д. 1",
                work_hours_ru="Пн-Пт: 10:00-20:00, Сб-Вс: 11:00-18:00",
            )
        return contact

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class FeedbackCreateView(viewsets.ModelViewSet):
    """Создать обратную связь"""

    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = FeedbackFilter

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
