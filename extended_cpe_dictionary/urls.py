"""
URL configuration for extended_cpe_dictionary project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView
from rest_framework import routers, serializers
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from application.urls import urlpatterns as application_urls
from application.views import *


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "is_staff"]


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)


# Routers provide an easy way of automatically determining the URL conf.
v1_router = routers.DefaultRouter()
v1_router.register("change-descriptions", CPEChangeDescriptionViewSet)
v1_router.register("checks", CPECheckViewSet)
v1_router.register("cpe-items", CPEItemViewSet)
v1_router.register("cpe23-items", CPE23ItemViewSet)
v1_router.register("deprecated-bys", CPEDeprecatedByViewSet)
v1_router.register("deprecations", CPEDeprecationViewSet)
v1_router.register("dictionaries", DictionaryViewSet)
v1_router.register("evidence-references", CPEEvidenceReferenceViewSet)
v1_router.register("generators", CPEGeneratorViewSet)
v1_router.register("notes", CPENoteViewSet)
v1_router.register("organizations", CPEOrganizationViewSet)
v1_router.register(
    "provenance-organization-participants", CPEProvenanceOrganizationParticipantViewSet
)
v1_router.register("provenance-records", CPEProvenanceRecordViewSet)
v1_router.register("references", CPEReferenceViewSet)
v1_router.register("titles", CPETitleViewSet)
v1_router.register("users", UserViewSet)
v1_router.register("wfns", CPEWellFormedNameViewSet)


urlpatterns = [
    path("", TemplateView.as_view(template_name="home_page.html")),
    path("admin/", admin.site.urls),
    path("select2/", include("django_select2.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/", RedirectView.as_view(url='/api/v1/', permanent=False)),
    path("api/v1/", include(v1_router.urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns.extend(application_urls)
