import json
import tarfile
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from application.models import *
from application.utilities.utils import cpe23_formatted_string_to_wfn, cpe23_to_cpe22


class Command(BaseCommand):
    help = (
        "Import CPE data from the NVD CPE Database tarball file."
        " [https://nvd.nist.gov/feeds/json/cpe/2.0/nvdcpe-2.0.tar.gz]"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "tarball_file",
            type=str,
            help="Path to the NVD CPE Database tarball file",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="Number of records to insert per batch.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tarball_file = Path(options["tarball_file"])

        if not tarball_file.exists():
            raise CommandError(f"File does not exist: {tarball_file}")
        with tarfile.open(tarball_file) as tar:
            for json_file in tarfile.open(tarball_file).getmembers():
                self.process_json(tar.extractfile(json_file))

    def process_json(self, json_file_object):
        try:
            data = json.load(json_file_object)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON: {exc}") from exc

        nvd_dictionary, created = CPEDictionary.objects.get_or_create(
            source_uri="https://nvd.nist.gov/feeds/json/cpe/2.0/nvdcpe-2.0.tar.gz"
        )
        try:
            generator = nvd_dictionary.generator
            generator.timestamp = data.get("timestamp")
            generator.save()
        except AttributeError:
            CPEGenerator(
                dictionary=nvd_dictionary,
                product_name=data.get("format"),
                product_version=data.get("version"),
                schema_version="2.3",
                timestamp=data.get("timestamp"),
            ).save()

        organization, created = CPEOrganization.objects.get_or_create(
            system_id="https://nvd.nist.gov", name="National Vulnerability Database"
        )

        products = data.get("products", [])
        if not isinstance(products, list):
            raise CommandError("'products' must be a list.")

        self.stdout.write(self.style.SUCCESS(f"Found {len(products):,} CPE records."))
        cpe_objects = {}
        cpe23_objects = {}
        title_objects = {}
        deprecation_objects = {}
        ref_objects = {}
        cpe_name_objects = {}
        for product in products:
            cpe_data = product.get("cpe")

            if not cpe_data:
                self.stdout.write(self.style.ERROR(f"invalid_product_data <{product}>"))
                continue

            cpe23_name = cpe_data.get("cpeName")
            cpe22_name = cpe23_to_cpe22(cpe23_name)
            cpe_name_uuid = cpe_data.get("cpeNameId")
            cpe_entry_last_modified = cpe_data.get("lastModified") + "Z"
            if not cpe23_name or not cpe_name_uuid:
                self.stderr.write(self.style.ERROR(f"invalid_cpe_data <{cpe_data}>"))
                continue

            cpe_item = CPEItem(
                cpe_name_id=cpe_name_uuid,
                dictionary=nvd_dictionary,
                name=cpe22_name,
                deprecated=cpe_data.get("deprecated"),
                updated_at=cpe_entry_last_modified,
                created_at=cpe_data.get("created") + "Z",
            )
            cpe_objects[cpe_name_uuid] = cpe_item
            cpe23_objects[cpe_name_uuid] = CPE23Item(name=cpe23_name)
            (
                part,
                vendor,
                product,
                version,
                update,
                edition,
                language,
                sw_edition,
                target_sw,
                target_hw,
                other,
            ) = cpe23_formatted_string_to_wfn(cpe23_name)
            cpe_name_objects[cpe_name_uuid] = CPEWellFormedName(
                part=part,
                vendor=vendor,
                product=product,
                version=version,
                update=update,
                edition=edition,
                language=language,
                sw_edition=sw_edition,
                target_sw=target_sw,
                target_hw=target_hw,
                other=other,
            )

            titles_data = cpe_data.get("titles", [])
            if titles_data:
                title_objects[cpe_name_uuid] = []
            for title_data in titles_data:
                title_objects[cpe_name_uuid].append(
                    CPETitle(
                        language=title_data.get("lang"), value=title_data.get("title")
                    )
                )
            refs_data = cpe_data.get("refs", [])
            if refs_data:
                ref_objects[cpe_name_uuid] = []
            for ref_data in refs_data:
                ref_objects[cpe_name_uuid].append(
                    CPEReference(
                        description=ref_data.get("type", "Unknown Reference"),
                        href=ref_data.get("ref"),
                    )
                )
            deprecated_items = cpe_data.get("deprecatedBy", [])
            if deprecated_items:
                deprecation_objects[cpe_name_uuid] = []
            for deprecation_data in deprecated_items:
                if deprecation_data.get("cpeNameId") is None:
                    print(f"ERROR deprecatedBy_invalid_data {deprecation_data}")
                    continue
                deprecation_name = deprecation_data.get("cpeName")
                deprecation_objects[cpe_name_uuid].append(
                    CPEDeprecatedBy(
                        deprecation_type=CPEDeprecatedBy.UNKNOWN, name=deprecation_name
                    )
                )

        cpe_items = CPEItem.objects.bulk_create(
            cpe_objects.values(),
            update_conflicts=True,
            update_fields=[
                _.name
                for _ in CPEItem._meta.get_fields()
                if _.concrete and not _.primary_key
            ],
            unique_fields=[
                _.name
                for _ in CPEItem._meta.get_fields()
                if hasattr(_, "unique") and _.unique
            ],
        )

        titles = []
        refs = []
        for cpe_item in cpe_items:
            for title_object in title_objects.get(cpe_item.cpe_name_id, []):
                title_object.item = cpe_item
                titles.append(title_object)
            for ref_object in ref_objects.get(cpe_item.cpe_name_id, []):
                ref_object.item = cpe_item
                refs.append(ref_object)

            cpe23_objects[cpe_item.cpe_name_id].item = cpe_item
        CPETitle.objects.bulk_create(titles, ignore_conflicts=True)
        del titles
        CPEReference.objects.bulk_create(
            refs,
            update_conflicts=True,
            update_fields=[
                _.name
                for _ in CPEReference._meta.get_fields()
                if _.concrete and not _.primary_key
            ],
            unique_fields=[
                _.name
                for _ in CPEReference._meta.get_fields()
                if hasattr(_, "unique") and _.unique
            ],
        )
        del refs
        cpe23_items = CPE23Item.objects.bulk_create(
            cpe23_objects.values(),
            update_conflicts=True,
            update_fields=["item"],
            unique_fields=["name"],
        )
        for cpe23_item in cpe23_items:
            cpe_name_objects[cpe23_item.item.cpe_name_id].cpe23_item = cpe23_item
        CPEWellFormedName.objects.bulk_create(
            cpe_name_objects.values(),
            update_conflicts=True,
            update_fields=[
                _.name
                for _ in CPEWellFormedName._meta.get_fields()
                if _.concrete and not _.primary_key
            ],
            unique_fields=["cpe23_item"],
        )
        deprecations = []
        provenances = []
        for cpe23_item in cpe23_items:
            if deprecation_objects.get(cpe23_item.item.cpe_name_id):
                deprecations.append(CPEDeprecation(cpe23_item=cpe23_item))

            try:
                provenance_record = cpe23_item.provenance
            except AttributeError:
                provenance_record = None
            if provenance_record is None:
                provenances.append(
                    CPEProvenanceRecord.objects.create(cpe23_item=cpe23_item)
                )

        deprecations = CPEDeprecation.objects.bulk_create(
            deprecations,
            update_conflicts=True,
            update_fields=[
                _.name
                for _ in CPEDeprecation._meta.get_fields()
                if _.concrete and not _.primary_key
            ],
            unique_fields=[
                _.name
                for _ in CPEDeprecation._meta.get_fields()
                if hasattr(_, "unique") and _.unique
            ],
        )
        deprecated_by_objects = []
        for deprecation in deprecations:
            for deprecation_object in deprecation_objects.get(
                deprecation.cpe23_item.item.cpe_name_id, []
            ):
                deprecation_object.deprecation = deprecation
                deprecated_by_objects.append(deprecation_object)
        CPEDeprecatedBy.objects.bulk_create(
            deprecated_by_objects,
            update_conflicts=True,
            update_fields=[
                _.name
                for _ in CPEDeprecatedBy._meta.get_fields()
                if _.concrete and not _.primary_key
            ],
            unique_fields=[
                _.name
                for _ in CPEDeprecatedBy._meta.get_fields()
                if hasattr(_, "unique") and _.unique
            ],
        )

        provenance_records = CPEProvenanceRecord.objects.bulk_create(
            provenances,
            update_conflicts=True,
            update_fields=["cpe23_item"],
            unique_fields=["id"],
        )

        authority_provenances = []
        for provenance_record in provenance_records:
            authority_provenance = provenance_record.organizations.filter(
                role=CPEProvenanceOrganizationParticipant.ROLE_AUTHORITY
            ).first()
            if not authority_provenance:
                authority_provenances.append(
                    CPEProvenanceOrganizationParticipant(
                        system_id=organization,
                        provenance=provenance_record,
                        role=CPEProvenanceOrganizationParticipant.ROLE_AUTHORITY,
                        date=provenance_record.cpe23_item.item.updated_at,
                    )
                )

            else:
                authority_provenance.date = provenance_record.cpe23_item.item.updated_at
                authority_provenances.append(authority_provenance)
        CPEProvenanceOrganizationParticipant.objects.bulk_create(
            authority_provenances,
            update_conflicts=True,
            update_fields=[
                _.name
                for _ in CPEProvenanceOrganizationParticipant._meta.get_fields()
                if _.concrete and not _.primary_key
            ],
            unique_fields=[
                _.name
                for _ in CPEProvenanceOrganizationParticipant._meta.get_fields()
                if hasattr(_, "unique") and _.unique
            ],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(cpe_objects):,} CPEs with {len(cpe_name_objects):,} names "
                f"and {len(title_objects):,} titles, and {len(ref_objects):,}"
                f" references and {len(deprecation_objects):,} deprecations."
            )
        )
