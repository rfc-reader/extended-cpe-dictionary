from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse

from django.urls import reverse_lazy
from django.views.generic import CreateView
from rest_framework import viewsets
from rest_framework.views import APIView

from .forms import CPEItemCreateForm, CPEItemDeprecateForm
from .models import *
from .serializers import *
from .utilities.regexes import (
    is_valid_avstring_regexed_string,
    is_valid_cpe23_regexed_string,
    is_valid_langtag_regexed_string,
)


class DictionaryViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict:cpe-list> views.
    """

    queryset = CPEDictionary.objects.all()
    serializer_class = CPEDictionarySerializer


class CPEEvidenceReferenceViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict:cpe-evidence-reference> views.
    """

    queryset = CPEEvidenceReference.objects.all()
    serializer_class = CPEEvidenceReferenceSerializer


class CPEChangeDescriptionViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict_ext:change-description> views.
    """

    queryset = CPEChangeDescription.objects.all()
    serializer_class = CPEChangeDescriptionSerializer


class CPECheckViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict:cpe-item> views.
    """

    queryset = CPECheck.objects.all()
    serializer_class = CPECheckSerializer


class CPEItemViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict:cpe-item> views.
    """

    queryset = CPEItem.objects.all()
    serializer_class = CPEItemSerializer


class CPE23ItemViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict:cpe23-item> views.
    """

    queryset = CPE23Item.objects.all()
    serializer_class = CPE23ItemSerializer


class CPEDeprecatedByViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict_ext:deprecatedBy> views.
    """

    queryset = CPEDeprecatedBy.objects.all()
    serializer_class = CPEDeprecatedBySerializer


class CPEDeprecationViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict_ext:deprecation> views.
    """

    queryset = CPEDeprecation.objects.all()
    serializer_class = CPEDeprecationSerializer


class CPEGeneratorViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict:generator> views.
    """

    queryset = CPEGenerator.objects.all()
    serializer_class = CPEGeneratorSerializer


class CPENoteViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict:notes> views.
    """

    queryset = CPENote.objects.all()
    serializer_class = CPENoteSerializer


class CPEOrganizationViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict:notes> views.
    """

    queryset = CPEOrganization.objects.all()
    serializer_class = CPEOrganizationSerializer


class CPEProvenanceOrganizationParticipantViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict_ext:title> views.
    """

    queryset = CPEProvenanceOrganizationParticipant.objects.all()
    serializer_class = CPEProvenanceOrganizationParticipantSerializer


class CPEProvenanceRecordViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict_ext:title> views.
    """

    queryset = CPEProvenanceRecord.objects.all()
    serializer_class = CPEProvenanceRecordSerializer


class CPEReferenceViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict_ext:title> views.
    """

    queryset = CPEReference.objects.all()
    serializer_class = CPEReferenceSerializer


class CPETitleViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the <cpe_dict_ext:title> views.
    """

    queryset = CPETitle.objects.all()
    serializer_class = CPETitleSerializer


class CPEWellFormedNameViewSet(viewsets.ModelViewSet):
    """
    This viewset provides the parsed CPEWellFormedName object views.
    """

    queryset = CPEWellFormedName.objects.all()
    serializer_class = CPEWellFormedNameSerializer


class CPEItemCreateView(CreateView):
    model = CPEItem
    form_class = CPEItemCreateForm
    template_name = "add_cpe_item.html"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form: CPEItemCreateForm):
        with transaction.atomic():
            # Create the CPE 2.2 dictionary item.
            self.object = form.save(commit=False)
            self.object.dictionary = self.form.dictionary
            self.object.save()
        messages.success(
            self.request,
            f"CPE item {self.object.name} was created successfully.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "cpeitem-detail",
            kwargs={
                "pk": self.object.pk,
            },
        )


class CuratedAddCPEItem(CreateView):
    model = CPEItem
    form_class = CPEItemCreateForm
    template_name = "add_cpe_item.html"

    def get_success_url(self):
        return reverse_lazy("cpeitem-detail", kwargs=dict(pk=self.object.pk))


class CuratedDeprecateCPEItem(CreateView):
    model = CPEItem
    form_class = CPEItemDeprecateForm
    template_name = "deprecate_cpe_item.html"

    def get_success_url(self):
        return reverse_lazy("cpeitem-detail", kwargs=dict(pk=self.object.pk))


class SelectCPE23FormattedString(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        results = (
            [
                {"id": item.name, "text": item.name}
                for item in CPE23Item.objects.filter(name__icontains=term)[:100]
            ]
            if len(term) < 2
            else []
        )
        if is_valid_cpe23_regexed_string(term):
            results.append({"id": term, "text": term})
        return JsonResponse({"results": results})


def _get_objects_by_filtered_terms(model_class, attribute, term, limit=1000):
    results = []
    filter_args = {f"{attribute}__icontains": term}
    for _ in model_class.objects.filter(**filter_args)[:limit]:
        results.append(getattr(_, attribute))
    if is_valid_avstring_regexed_string(term):
        results.append(term)
    results = sorted(set(results))
    return JsonResponse(
        {"results": [{"id": result, "text": result} for result in results]}
    )


class SelectVendor(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        return _get_objects_by_filtered_terms(CPEWellFormedName, "vendor", term)


class SelectProduct(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        return _get_objects_by_filtered_terms(CPEWellFormedName, "product", term)


class SelectVersion(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        return _get_objects_by_filtered_terms(CPEWellFormedName, "version", term)


class SelectUpdate(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        return _get_objects_by_filtered_terms(CPEWellFormedName, "update", term)


class SelectLanguage(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        results = []
        filter_args = {"language__icontains": term}
        for _ in CPEWellFormedName.objects.filter(**filter_args)[:1000]:
            results.append(_.language)
        if is_valid_langtag_regexed_string(term):
            results.append(term)
        results = sorted(set(results))
        return JsonResponse(
            {"results": [{"id": result, "text": result} for result in results]}
        )


class SelectSoftwareEdition(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        return _get_objects_by_filtered_terms(CPEWellFormedName, "sw_edition", term)


class SelectTargetSoftware(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        return _get_objects_by_filtered_terms(CPEWellFormedName, "target_sw", term)


class SelectTargetHardware(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        return _get_objects_by_filtered_terms(CPEWellFormedName, "target_hw", term)


class SelectOther(APIView):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "")
        return _get_objects_by_filtered_terms(CPEWellFormedName, "other", term)
