import datetime
import uuid

from django import forms
from django.core.validators import RegexValidator
from django.db import transaction
from django_select2 import forms as s2forms

from .models import (
    CPE23Item,
    CPEChangeDescription,
    CPEDeprecatedBy,
    CPEDeprecation,
    CPEDictionary,
    CPEEvidenceReference,
    CPEItem,
    CPEOrganization,
    CPEWellFormedName,
)
from .serializers import CPEItemSerializer
from .utilities.regexes import (
    avstring_regex,
    cpe23_regex,
    is_valid_cpe23_regexed_string,
    langtag_regex,
)


class CPEItemWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "cpe23__name__icontains",
    ]


class CPEItemCreateForm(forms.ModelForm):
    dictionary = forms.ModelChoiceField(queryset=CPEDictionary.objects.all())
    authority = forms.ModelChoiceField(queryset=CPEOrganization.objects.all())
    submitter = forms.ModelChoiceField(queryset=CPEOrganization.objects.all())
    title = forms.CharField(
        max_length=4096,
        help_text="Human-readable title of the name.",
        widget=forms.TextInput(),
    )
    part = forms.ChoiceField(
        choices=CPEWellFormedName.PART_CHOICES,
    )
    vendor = forms.ChoiceField(
        help_text="The vendor that develops or owns the product.",
        validators=[RegexValidator(regex=avstring_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-vendor", attrs=dict(style="width:50%")
        ),
    )
    product = forms.ChoiceField(
        help_text="The product field.",
        validators=[RegexValidator(regex=avstring_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-product", attrs=dict(style="width:50%")
        ),
    )
    version = forms.ChoiceField(
        help_text="The version field.",
        validators=[RegexValidator(regex=avstring_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-version", attrs=dict(style="width:50%")
        ),
    )
    update = forms.ChoiceField(
        help_text="The update field.",
        validators=[RegexValidator(regex=avstring_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-update", attrs=dict(style="width:50%")
        ),
    )
    language = forms.ChoiceField(
        help_text="The language field.",
        validators=[RegexValidator(regex=langtag_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-language", attrs=dict(style="width:50%")
        ),
    )
    sw_edition = forms.ChoiceField(
        help_text="The sw_edition field.",
        validators=[RegexValidator(regex=avstring_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-sw-edition", attrs=dict(style="width:50%")
        ),
    )
    target_sw = forms.ChoiceField(
        help_text="The target_sw field.",
        validators=[RegexValidator(regex=avstring_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-target-sw", attrs=dict(style="width:50%")
        ),
    )
    target_hw = forms.ChoiceField(
        help_text="The target_hw field.",
        validators=[RegexValidator(regex=avstring_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-target-hw", attrs=dict(style="width:50%")
        ),
    )
    other = forms.ChoiceField(
        help_text="The other field.",
        validators=[RegexValidator(regex=avstring_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-other", attrs=dict(style="width:50%")
        ),
    )
    note = forms.CharField(
        max_length=4096,
        required=False,
        help_text="Optional descriptive material for the new CPE.",
        widget=forms.Textarea,
    )
    comments = forms.CharField(
        max_length=4096,
        widget=forms.Textarea,
        required=False,
        help_text="Comments explaining the rationale for the new item.",
    )

    class Meta:
        model = CPEItem

        fields = [
            "dictionary",
            "authority",
            "submitter",
            "part",
            "vendor",
            "product",
            "version",
            "update",
            "language",
            "sw_edition",
            "target_sw",
            "target_hw",
            "other",
            "title",
            "note",
            "comments",
        ]

    def save(self, *args, **kwargs):
        if self.errors:
            raise ValueError(str(self.errors))

        cpe_name_id = str(uuid.uuid4())
        now = datetime.datetime.now(tz=datetime.UTC)
        validated_data = dict(
            cpe23=dict(
                name=self.cleaned_data["cpe23_name"],
                provenance=dict(
                    organizations=[
                        dict(
                            date=now,
                            role="authority",
                            system_id=self.cleaned_data["authority"],
                        ),
                        dict(
                            date=now,
                            role="submitter",
                            system_id=self.cleaned_data["submitter"],
                        ),
                    ],
                    changes=[
                        dict(
                            change_type="ORIGINAL_RECORD",
                            comments=self.cleaned_data["comments"],
                            date=now,
                        )
                    ],
                ),
            ),
            cpe_name_id=cpe_name_id,
            dictionary=self.cleaned_data["dictionary"],
        )
        note = self.cleaned_data.get("note")
        if note:
            validated_data["notes"] = [
                dict(language=self.cleaned_data["language"], value=note)
            ]
        title = self.cleaned_data.get("title")
        if title:
            validated_data["titles"] = [
                dict(language=self.cleaned_data["language"], value=title)
            ]
        self.instance = CPEItemSerializer().create(validated_data=validated_data)
        return self.instance


def get_dynamic_choices():
    # Fetch choices dynamically from your model
    return [(obj.name, obj.name) for obj in CPE23Item.objects.all()]


class CPEItemDeprecateForm(forms.ModelForm):
    class Meta:
        model = CPEItem

        fields = [
            "item",
            "depreciation_reason",
            "deprecated_by",
        ]

    item = forms.ModelChoiceField(
        queryset=CPEItem.objects.filter(deprecated=False),
        widget=s2forms.ModelSelect2Widget(
            attrs=dict(
                style="width:50%",
            ),
            model=CPEItem,
            search_fields=[
                "cpe23__name__icontains",
            ],
        ),
    )
    depreciation_reason = forms.ChoiceField(
        choices=CPEDeprecatedBy.DEPRECATION_TYPE_CHOICES
    )
    deprecated_by = forms.ChoiceField(
        help_text="The CPE formatted string that deprecates this one.",
        label="Deprecated By",
        validators=[RegexValidator(regex=cpe23_regex)],
        widget=s2forms.HeavySelect2Widget(
            data_view="select-cpename", attrs=dict(style="width:50%")
        ),
    )
    comments = forms.CharField(
        help_text="Comments explaining the rationale for the deprecation.",
        max_length=4096,
        required=False,
        widget=forms.Textarea,
    )
    evidence_href = forms.CharField(
        help_text="A link to external information relating to the change, if available.",
        label="Evidence Link",
        max_length=4096,
        required=False,
    )
    evidence_type = forms.ChoiceField(
        choices=CPEEvidenceReference.EVIDENCE_CHOICES,
        help_text="Evidence Type that led to the deprecation.",
    )

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.errors:
            raise ValueError(str(self.errors))
        now = datetime.datetime.now(tz=datetime.UTC)
        cpe_item: CPEItem = self.cleaned_data["item"]
        cpe_item.deprecated = True
        cpe_item.deprecation_date = now
        cpe_item.save()
        deprecation = CPEDeprecation.objects.create(
            cpe23_item=cpe_item.cpe23,
            date=now,
        )
        CPEDeprecatedBy.objects.create(
            deprecation=deprecation,
            name=self.cleaned_data["deprecated_by"],
            deprecation_type=self.cleaned_data["depreciation_reason"],
        )
        change_description = CPEChangeDescription.objects.create(
            change_type=CPEChangeDescription.DEPRECATION,
            comments=self.cleaned_data["comments"],
            date=now,
            provenance=cpe_item.cpe23.provenance,
        )
        evidence_href = self.cleaned_data.get("evidence_href")
        if evidence_href:
            CPEEvidenceReference.objects.create(
                change=change_description,
                href=evidence_href,
                evidence=self.cleaned_data["evidence_type"],
            )
        self.instance = cpe_item
        return self.instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "data"):
            deprecated_by = self.data.get("deprecated_by", [])
            if deprecated_by:
                if is_valid_cpe23_regexed_string(deprecated_by):
                    self.fields["deprecated_by"].choices = [
                        (deprecated_by, deprecated_by)
                    ]
