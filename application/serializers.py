from django.db import transaction
from rest_framework import serializers

from .models import *

__all__ = (
    "CPE23ItemSerializer",
    "CPEChangeDescriptionSerializer",
    "CPECheckSerializer",
    "CPEDeprecatedBySerializer",
    "CPEDeprecationSerializer",
    "CPEDictionarySerializer",
    "CPEEvidenceReferenceSerializer",
    "CPEGeneratorSerializer",
    "CPEItemSerializer",
    "CPENoteSerializer",
    "CPEOrganizationSerializer",
    "CPEProvenanceOrganizationParticipantSerializer",
    "CPEProvenanceRecordSerializer",
    "CPEReferenceSerializer",
    "CPETitleSerializer",
    "CPEWellFormedNameSerializer",
)

from application.utilities.utils import cpe23_to_cpe22


class CPEGeneratorInlineSerializer(serializers.ModelSerializer):
    class Meta:
        extra_kwargs = dict(
            product_name=dict(required=False), product_version=dict(required=False)
        )
        fields = (
            "id",
            "product_name",
            "product_version",
            "schema_version",
            "timestamp",
        )
        model = CPEGenerator
        optional_fields = ("product_name", "product_version")


class CPETitleInlineSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "language",
            "value",
        )
        model = CPETitle


class CPENoteInlineSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "language",
            "value",
        )
        model = CPENote


class CPEReferenceInlineSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "description",
            "href",
        )
        model = CPEReference


class CPEEvidenceReferenceInlineSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("evidence", "href")
        model = CPEEvidenceReference


class CPEChangeDescriptionInlineSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "change_type",
            "date",
            "comments",
            "evidence",
        )
        model = CPEChangeDescription
        read_only_fields = ()

    evidence = CPEEvidenceReferenceInlineSerializer(
        many=False, read_only=False, required=False
    )


class CPECheckInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPECheck
        fields = (
            "system",
            "check_id",
            "file",
        )


class CPEDeprecatedByInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEDeprecatedBy
        fields = (
            "name",
            "deprecation_type",
        )


class DeprecationsListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        objects = (CPEDeprecation(**item) for item in validated_data)
        return CPEDeprecation.objects.bulk_create(objects)


class CPEProvenanceOrganizationParticipantInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEProvenanceOrganizationParticipant
        fields = (
            "role",
            "system_id",
            "date",
        )


class CPEDeprecationInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEDeprecation
        list_serializer_class = DeprecationsListSerializer
        fields = (
            "date",
            "created_at",
            "deprecated_by",
        )

    deprecated_by = CPEDeprecatedByInlineSerializer(many=True, read_only=False)


class CPEProvenanceRecordInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEProvenanceRecord
        fields = ("created_at", "changes", "organizations")

    changes = CPEChangeDescriptionInlineSerializer(
        many=True, read_only=False, required=False
    )
    organizations = CPEProvenanceOrganizationParticipantInlineSerializer(
        many=True, read_only=False, required=False
    )


class CPEWellFormedNameInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEWellFormedName
        fields = (
            "part",
            "vendor",
            "product",
            "version",
            "update",
            "edition",
            "language",
            "sw_edition",
            "target_sw",
            "target_hw",
            "other",
        )


class CPE23ItemInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPE23Item
        fields = (
            "deprecations",
            "name",
            "provenance",
            "wfn",
        )

    deprecations = CPEDeprecationInlineSerializer(
        many=True, read_only=False, required=False
    )
    provenance = CPEProvenanceRecordInlineSerializer(many=False, read_only=False)
    wfn = CPEWellFormedNameInlineSerializer(many=False, read_only=True)


# Primary Serializers


class CPE23ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPE23Item
        fields = (
            "id",
            "name",
            "item",
            "deprecations",
            "provenance",
            "wfn",
        )
        read_only_fields = ("id",)

    deprecations = CPEDeprecationInlineSerializer(
        many=True, read_only=False, required=False
    )
    provenance = CPEProvenanceRecordInlineSerializer(many=False, read_only=False)
    wfn = CPEWellFormedNameInlineSerializer(many=False, read_only=True)

    @classmethod
    def handle_cpe23_data(cls, validated_data, item=None):
        deprecation_data = (
            validated_data.pop("deprecations")
            if "deprecations" in validated_data
            else []
        )
        provenance_data = (
            validated_data.pop("provenance") if "provenance" in validated_data else []
        )
        cpe23_item = CPE23Item.objects.create(item=item, **validated_data)
        CPEWellFormedName.create_from_cpe23_model(cpe23_item)
        if deprecation_data:
            for deprecation in deprecation_data:
                CPEDeprecationSerializer.handle_deprecation_data(
                    deprecation, cpe23_item=cpe23_item
                )
        if provenance_data:
            CPEProvenanceRecordSerializer.handle_provenance_record_data(
                provenance_data, cpe23_item=cpe23_item
            )

    @transaction.atomic
    def create(self, validated_data):
        return self.handle_cpe23_data(validated_data)


class CPEChangeDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        extra_kwargs = dict(provenance=dict(required=False))
        fields = (
            "id",
            "change_type",
            "date",
            "comments",
            "provenance",
            "evidence",
        )
        model = CPEChangeDescription
        read_only_fields = ("id",)

    evidence = CPEEvidenceReferenceInlineSerializer(
        many=False, read_only=False, required=False
    )

    @classmethod
    def handle_change_description_data(cls, validated_data, provenance=None):
        evidence_data = (
            validated_data.pop("evidence") if "evidence" in validated_data else None
        )
        change_description = CPEChangeDescription.objects.create(
            provenance=provenance, **validated_data
        )
        if evidence_data:
            CPEEvidenceReference.objects.create(
                change=change_description, **evidence_data
            )
        return change_description

    def create(self, validated_data):
        return self.handle_change_description_data(validated_data)


class CPECheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPECheck
        fields = (
            "id",
            "system",
            "check_id",
            "file",
            "item",
        )
        read_only_fields = ("id",)


class CPEDeprecatedBySerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEDeprecatedBy
        fields = (
            "id",
            "deprecation_type",
            "name",
            "deprecation",
        )
        read_only_fields = ("id",)


class CPEDeprecationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEDeprecation
        fields = (
            "id",
            "created_at",
            "date",
            "deprecated_by",
            "cpe23_item",
        )
        read_only_fields = ("created_at",)

    deprecated_by = CPEDeprecatedByInlineSerializer(
        many=True, read_only=False, required=False
    )

    @classmethod
    def handle_deprecation_data(cls, validated_data, cpe23_item=None):
        deprecated_by_data = validated_data.pop("deprecated_by")
        deprecation = CPEDeprecation.objects.create(
            cpe23_item=cpe23_item, **validated_data
        )
        for deprecated_by in deprecated_by_data:
            CPEDeprecatedBy.objects.create(deprecation=deprecation, **deprecated_by)
        return deprecation

    def create(self, validated_data):
        return self.handle_deprecation_data(validated_data)


class CPEDictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEDictionary
        fields = ("id", "source_uri", "imported_at", "generator")

    generator = CPEGeneratorInlineSerializer(
        many=False, read_only=False, required=False
    )

    def create(self, validated_data):
        generator_data = (
            validated_data.pop("generator") if "generator" in validated_data else None
        )
        dictionary = CPEDictionary.objects.create(**validated_data)
        if generator_data:
            CPEGenerator.objects.create(dictionary=dictionary, **generator_data)
        return dictionary


class CPEEvidenceReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEEvidenceReference
        fields = ("id", "evidence", "href", "change")
        read_only_fields = ("id",)


class CPEGeneratorSerializer(serializers.ModelSerializer):
    class Meta:
        extra_kwargs = dict(
            product_name=dict(required=False), product_version=dict(required=False)
        )
        fields = (
            "id",
            "product_name",
            "product_version",
            "schema_version",
            "timestamp",
            "dictionary",
        )
        model = CPEGenerator
        read_only_fields = ("id",)


class CPEItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPEItem
        fields = (
            "deprecated",
            "deprecated_by_cpe22",
            "deprecation_date",
            "dictionary",
            "name",
            "updated_at",
            "created_at",
            "cpe_name_id",
            "cpe23",
            "titles",
            "notes",
            "references",
            "checks",
        )
        read_only_fields = (
            "name",
            "deprecated_by_cpe22",
            "deprecation_date",
        )

    checks = CPECheckInlineSerializer(many=True, read_only=False, required=False)
    cpe23 = CPE23ItemInlineSerializer(many=False, read_only=False, required=True)
    notes = CPENoteInlineSerializer(many=True, read_only=False, required=False)
    references = CPEReferenceInlineSerializer(
        many=True, read_only=False, required=False
    )
    titles = CPETitleInlineSerializer(many=True, read_only=False, required=False)

    @transaction.atomic
    def create(self, validated_data):
        checks_data = validated_data.pop("checks") if "checks" in validated_data else []
        cpe23_data = validated_data.pop("cpe23")
        notes_data = validated_data.pop("notes") if "notes" in validated_data else []
        references_data = (
            validated_data.pop("references") if "references" in validated_data else []
        )
        titles_data = validated_data.pop("titles") if "titles" in validated_data else []
        name = cpe23_to_cpe22(cpe23_data.get("name"))
        cpe_item = CPEItem.objects.create(name=name, **validated_data)
        for data in checks_data:
            CPECheck.objects.create(item=cpe_item, **data)
        CPE23ItemSerializer.handle_cpe23_data(cpe23_data, item=cpe_item)
        for notes in notes_data:
            CPENote.objects.create(item=cpe_item, **notes)
        for data in references_data:
            CPEReference.objects.create(item=cpe_item, **data)
        for data in titles_data:
            CPETitle.objects.create(item=cpe_item, **data)

        return cpe_item


class CPENoteSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "language",
            "value",
            "item",
        )
        model = CPENote
        read_only_fields = ("id",)


class CPEOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        extra_kwargs = dict(description=dict(required=False))
        fields = (
            "id",
            "system_id",
            "name",
            "description",
        )
        model = CPEOrganization
        read_only_fields = ("id",)


class CPEProvenanceOrganizationParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "role",
            "system_id",
            "date",
            "provenance",
        )
        model = CPEProvenanceOrganizationParticipant
        read_only_fields = ("id",)


class CPEProvenanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "created_at",
            "cpe23_item",
            "organizations",
            "changes",
        )
        model = CPEProvenanceRecord
        read_only_fields = ("id",)

    changes = CPEChangeDescriptionInlineSerializer(
        many=True, read_only=False, required=False
    )
    organizations = CPEProvenanceOrganizationParticipantInlineSerializer(
        many=True, read_only=False, required=False
    )

    @classmethod
    def handle_provenance_record_data(cls, validated_data, cpe23_item=None):
        changes_data = (
            validated_data.pop("changes") if "changes" in validated_data else []
        )
        organizations_data = (
            validated_data.pop("organizations")
            if "organizations" in validated_data
            else []
        )
        provenance_record = CPEProvenanceRecord.objects.create(
            cpe23_item=cpe23_item, **validated_data
        )
        for data in changes_data:
            CPEChangeDescriptionSerializer.handle_change_description_data(
                data, provenance=provenance_record
            )
        for data in organizations_data:
            CPEProvenanceOrganizationParticipant.objects.create(
                provenance=provenance_record, **data
            )
        return provenance_record

    def create(self, validated_data):
        return self.handle_provenance_record_data(validated_data)


class CPEReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "description",
            "href",
            "item",
        )
        model = CPEReference
        read_only_fields = ("id",)


class CPETitleSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "language",
            "value",
            "item",
        )
        model = CPETitle
        read_only_fields = ("id",)


class CPEWellFormedNameSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "part",
            "vendor",
            "product",
            "version",
            "update",
            "edition",
            "language",
            "sw_edition",
            "target_sw",
            "target_hw",
            "other",
            "cpe23_item",
        )
        model = CPEWellFormedName
        read_only_fields = ("id",)
