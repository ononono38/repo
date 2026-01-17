from django.urls import path
from app import views

urlpatterns = [
    path("sessions", views.SessionCreateView.as_view()),
    path("sessions/<uuid:session_id>", views.SessionRetrieveView.as_view()),
    path("sessions/<uuid:session_id>/member-lookup", views.MemberLookupView.as_view()),
    path("sessions/<uuid:session_id>/order", views.OrderCreateView.as_view()),
]
