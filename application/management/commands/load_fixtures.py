import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from application.models import *
from application.serializers import CPEDictionarySerializer, CPEItemSerializer


class Command(BaseCommand):
    help = "Load test fixtures to the database."

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="Path to the json file")

    def handle(self, *args, **options):
        json_file = Path(options["json_file"])

        if not json_file.exists():
            raise CommandError(f"File does not exist: {json_file}")
        with json_file.open() as json_file:
            json_data = json.load(json_file)
        self.process_json(json_data)

    @transaction.atomic
    def process_json(self, data):
        test_organization, _ = CPEOrganization.objects.get_or_create(
            system_id="urn://cpe-org/test-org", name="Test Organization"
        )
        cpe_items = data.pop("cpe-items") if data.get("cpe-items") else []
        test_dictionary = CPEDictionarySerializer().create(data)
        for cpe_item in cpe_items:
            cpe_item["dictionary"] = test_dictionary
            for organization in (
                cpe_item.get("cpe23", {}).get("provenance", {}).get("organizations", [])
            ):
                organization["system_id"] = test_organization
            CPEItemSerializer().create(cpe_item)
