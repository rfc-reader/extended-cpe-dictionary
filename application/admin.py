from django.contrib import admin
from nested_admin.nested import (
    NestedModelAdmin,
    NestedStackedInline,
    NestedTabularInline,
)

from .models import (
    CPE23Item,
    CPEChangeDescription,
    CPECheck,
    CPEDeprecatedBy,
    CPEDeprecation,
    CPEDictionary,
    CPEEvidenceReference,
    CPEGenerator,
    CPEItem,
    CPENote,
    CPEOrganization,
    CPEProvenanceOrganizationParticipant,
    CPEProvenanceRecord,
    CPEReference,
    CPETitle,
    CPEWellFormedName,
)

# ---------------------------------------------------------------------------
# Dictionary
# ---------------------------------------------------------------------------


class CPEGeneratorInline(NestedStackedInline):
    extra = 0
    max_num = 1
    model = CPEGenerator


@admin.register(CPEDictionary)
class CPEDictionaryAdmin(NestedModelAdmin):
    date_hierarchy = "imported_at"
    inlines = (CPEGeneratorInline,)
    list_display = (
        "id",
        "source_uri",
        "imported_at",
        "generator__timestamp",
        "generator__product_name",
        "generator__product_version",
        "generator__schema_version",
    )
    list_display_links = ["id"]
    readonly_fields = ("imported_at",)
    search_fields = ("source_uri",)


@admin.register(CPEGenerator)
class CPEGeneratorAdmin(NestedModelAdmin):
    date_hierarchy = "timestamp"
    list_display = (
        "id",
        "product_name",
        "product_version",
        "schema_version",
        "dictionary",
        "timestamp",
    )
    list_display_links = ["id"]


# ---------------------------------------------------------------------------
# CPE Item metadata
# ---------------------------------------------------------------------------


class CPETitleInline(NestedTabularInline):
    extra = 0
    model = CPETitle


class CPENoteInline(NestedTabularInline):
    extra = 0
    model = CPENote


class CPEReferenceInline(NestedTabularInline):
    extra = 0
    model = CPEReference


class CPECheckInline(NestedTabularInline):
    extra = 0
    model = CPECheck


class CPEDeprecatedByInline(NestedTabularInline):
    extra = 0
    model = CPEDeprecatedBy


class CPEDeprecationInline(NestedStackedInline):
    extra = 0
    inlines = (CPEDeprecatedByInline,)
    model = CPEDeprecation
    readonly_fields = ("created_at",)
    show_change_link = True


class CPEProvenanceOrganizationParticipantInline(NestedTabularInline):
    extra = 0
    model = CPEProvenanceOrganizationParticipant


class CPEEvidenceReferenceInline(NestedStackedInline):
    extra = 0
    max_num = 1
    model = CPEEvidenceReference


class CPEChangeDescriptionInline(NestedStackedInline):
    extra = 0
    inlines = (CPEEvidenceReferenceInline,)
    model = CPEChangeDescription
    show_change_link = True


class CPEProvenanceRecordInline(NestedStackedInline):
    extra = 0
    inlines = (
        CPEProvenanceOrganizationParticipantInline,
        CPEChangeDescriptionInline,
    )
    max_num = 1
    model = CPEProvenanceRecord
    show_change_link = True


class CPEWellFormedNameInline(NestedStackedInline):
    extra = 0
    fieldsets = (
        ("CPE Identity", dict(fields=("part", "vendor", "product", "version"))),
        (
            "Version / Edition",
            dict(fields=("update", "edition", "language", "sw_edition")),
        ),
        ("Target", dict(fields=("target_sw", "target_hw", "other"))),
    )
    max_num = 1
    model = CPEWellFormedName


class CPE23ItemInline(NestedStackedInline):
    extra = 0
    fields = ("name",)
    inlines = (
        CPEDeprecationInline,
        CPEProvenanceRecordInline,
        CPEWellFormedNameInline,
    )
    list_select_related = (
        "dictionary",
        "cpe23",
        "wfn",
    )
    max_num = 1
    model = CPE23Item
    show_change_link = False


@admin.register(CPEItem)
class CPEItemAdmin(NestedModelAdmin):
    autocomplete_fields = ("dictionary",)
    date_hierarchy = "created_at"
    fieldsets = (
        (
            "CPE Identity",
            {
                "fields": (
                    "cpe_name_id",
                    "deprecated",
                    "dictionary",
                    "name",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    inlines = (
        CPECheckInline,
        CPE23ItemInline,
        CPENoteInline,
        CPEReferenceInline,
        CPETitleInline,
    )
    list_display = (
        "cpe_name_id",
        "cpe23",
        "deprecated",
        "deprecation_date",
        "name",
        "deprecated_by_cpe22",
        "created_at",
        "updated_at",
    )
    list_display_links = ["cpe_name_id"]
    list_filter = (
        "deprecated",
        "dictionary__source_uri",
        "deprecation_date",
        "cpe23__wfn__part",
    )
    list_select_related = (
        "dictionary",
        "cpe23",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    search_fields = (
        "cpe23__name",
        "cpe23__wfn__vendor",
        "cpe23__wfn__product",
        "cpe23__wfn__version",
        "titles__value",
    )


@admin.register(CPE23Item)
class CPE23ItemAdmin(NestedModelAdmin):
    autocomplete_fields = ("item",)
    inlines = (
        CPEWellFormedNameInline,
        CPEDeprecationInline,
        CPEProvenanceRecordInline,
    )
    list_display = (
        "name",
        "item",
    )
    search_fields = (
        "name",
        "item__name",
        "item__titles__value",
    )


class CPEOrganizationInline(NestedTabularInline):
    extra = 0
    model = CPEOrganization


@admin.register(CPEProvenanceRecord)
class CPEProvenanceRecordAdmin(NestedModelAdmin):
    autocomplete_fields = ("cpe23_item",)
    inlines = (
        CPEProvenanceOrganizationParticipantInline,
        CPEChangeDescriptionInline,
    )
    list_display = (
        "id",
        "cpe23_item",
        "created_at",
    )
    readonly_fields = ("created_at",)
    search_fields = (
        "cpe23_item__name",
        "cpe23_item__item__name",
    )


@admin.register(CPEOrganization)
class CPEOrganizationAdmin(NestedModelAdmin):
    list_display = (
        "id",
        "system_id",
        "name",
        "description",
    )
    search_fields = (
        "description",
        "name",
        "system_id",
    )


@admin.register(CPEProvenanceOrganizationParticipant)
class CPEProvenanceOrganizationParticipantAdmin(NestedModelAdmin):
    autocomplete_fields = ("provenance",)
    list_display = (
        "id",
        "role",
        "system_id",
        "date",
        "provenance",
    )
    list_filter = ("role",)


@admin.register(CPEChangeDescription)
class CPEChangeDescriptionAdmin(NestedModelAdmin):
    autocomplete_fields = ("provenance",)
    inlines = (CPEEvidenceReferenceInline,)
    list_display = (
        "id",
        "change_type",
        "date",
        "provenance",
    )
    list_filter = ("change_type",)
    search_fields = ("comments",)


@admin.register(CPEEvidenceReference)
class CPEEvidenceReferenceAdmin(NestedModelAdmin):
    list_display = (
        "id",
        "change",
        "evidence",
        "href",
    )
    list_filter = ("evidence",)
    search_fields = (
        "change__comments",
        "href",
    )


@admin.register(CPEDeprecation)
class CPEDeprecationAdmin(NestedModelAdmin):
    autocomplete_fields = ("cpe23_item",)
    inlines = (CPEDeprecatedByInline,)
    list_display = (
        "cpe23_item",
        "date",
        "created_at",
    )
    readonly_fields = ("created_at",)
    search_fields = ("cpe23_item__name",)


@admin.register(CPEDeprecatedBy)
class CPEDeprecatedByAdmin(NestedModelAdmin):
    autocomplete_fields = ("deprecation",)
    list_display = (
        "id",
        "name",
        "deprecation_type",
        "deprecation",
    )
    list_filter = ("deprecation_type",)
    search_fields = (
        "name",
        "deprecation__cpe23_item__name",
    )


@admin.register(CPETitle)
class CPETitleAdmin(NestedModelAdmin):
    autocomplete_fields = ("item",)
    list_display = (
        "id",
        "value",
        "language",
        "item",
    )
    list_filter = ("language",)
    search_fields = (
        "value",
        "item__cpe23__name",
    )


@admin.register(CPENote)
class CPENoteAdmin(NestedModelAdmin):
    autocomplete_fields = ("item",)
    list_display = (
        "id",
        "short_value",
        "language",
        "item",
    )
    list_filter = ("language",)
    search_fields = (
        "value",
        "item__name",
        "item__cpe23__name",
    )

    @admin.display(description="Note")
    def short_value(self, obj):
        return obj.value[:100]


@admin.register(CPEReference)
class CPEReferenceAdmin(NestedModelAdmin):
    autocomplete_fields = ("item",)
    list_display = (
        "id",
        "href",
        "description",
        "item",
    )
    search_fields = (
        "description",
        "href",
        "item__cpe23__name",
        "item__name",
    )


@admin.register(CPECheck)
class CPECheckAdmin(NestedModelAdmin):
    autocomplete_fields = ("item",)
    list_display = (
        "id",
        "system",
        "check_id",
        "file",
        "item",
    )
    search_fields = (
        "check_id",
        "item__cpe23__name",
        "item__name",
        "system",
    )


@admin.register(CPEWellFormedName)
class CPEWellFormedNameAdmin(NestedModelAdmin):
    autocomplete_fields = ("cpe23_item",)
    fieldsets = (
        ("CPE Identity", dict(fields=("part", "vendor", "product", "version"))),
        (
            "Version / Edition",
            dict(fields=("update", "edition", "language", "sw_edition")),
        ),
        ("Target", dict(fields=("target_sw", "target_hw", "other"))),
    )
    list_display = (
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
    )
    list_filter = ("part",)
    readonly_fields = (
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
    search_fields = (
        "part",
        "product",
        "vendor",
    )
