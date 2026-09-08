from django.urls import path

from .views import (
    CuratedAddCPEItem,
    CuratedDeprecateCPEItem,
    SelectCPE23FormattedString,
    SelectLanguage,
    SelectOther,
    SelectProduct,
    SelectSoftwareEdition,
    SelectTargetHardware,
    SelectTargetSoftware,
    SelectUpdate,
    SelectVendor,
    SelectVersion,
)

urlpatterns = [
    path("curation/add-cpe-item", CuratedAddCPEItem.as_view(), name="item-create"),
    path(
        "curation/deprecate-cpe-item",
        CuratedDeprecateCPEItem.as_view(),
        name="item-deprecate",
    ),
    path(
        "api/v1/selection/cpenames",
        SelectCPE23FormattedString.as_view(),
        name="select-cpename",
    ),
    path(
        "api/v1/selection/vendors",
        SelectVendor.as_view(),
        name="select-vendor",
    ),
    path("api/v1/selection/product", SelectProduct.as_view(), name="select-product"),
    path("api/v1/selection/version", SelectVersion.as_view(), name="select-version"),
    path("api/v1/selection/update", SelectUpdate.as_view(), name="select-update"),
    path("api/v1/selection/language", SelectLanguage.as_view(), name="select-language"),
    path(
        "api/v1/selection/sw-edition",
        SelectSoftwareEdition.as_view(),
        name="select-sw-edition",
    ),
    path(
        "api/v1/selection/target-sw",
        SelectTargetSoftware.as_view(),
        name="select-target-sw",
    ),
    path(
        "api/v1/selection/target-hw",
        SelectTargetHardware.as_view(),
        name="select-target-hw",
    ),
    path("api/v1/selection/other", SelectOther.as_view(), name="select-other"),
]
