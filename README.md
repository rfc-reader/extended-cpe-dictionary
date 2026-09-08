# What is this?

A local instance of a CPE dictionary as described by the [NIST IR 7697](https://csrc.nist.gov/pubs/ir/7697/final)
Common Platform Enumeration: Dictionary Specification Version 2.3

# Quick Start

```
docker build -t extended-cpe-dictionary .
docker run --rm -it -d --name local-cpe-dict -p 8000:8000 extended-cpe-dictionary
# browse to http://localhost:8000

# To add an admin account
docker exec -it local-cpe-dict uv run python manage.py createsuperuser

# To load some exemplar data
docker exec local-cpe-dict uv run python manage.py load_fixtures application/management/commands/test_data.json
```

# Why wouldn't I use the [Official CPE Dictionary](https://nvd.nist.gov/cpe.cfm)?

You should. However, per the Introduction of NIST IR 7697:

```
Organizations may create their own extended CPE dictionaries, which are used to store identifier names
not present in the Official CPE Dictionary. There are several reasons why extended dictionaries are
needed. For example, an organization may have to create identifier names for proprietary products that
are only useful within that organization, such as internally developed software not found outside the
organization. Another possible reason is that an IT company may want to use identifiers for their
unreleased products that do not yet have official identifier names; once the identifier names have
stabilized, the company would submit them to the Official CPE Dictionary. Finally, an organization may
discover new products in use that do not yet have official identifiers; the organization could create
identifiers, add them to its own extended dictionary, submit them for inclusion in the Official CPE
Dictionary, and use them internally while waiting for their addition to the Official CPE Dictionary.
```

# Is this project authorized or affiliated with NIST, NVD, SCAP, etc... in any way?

No. However, without those organizations this project would not exist.

Nani Gigantum Humeris Insidentes.

# Why doesn't this project do >insert feature here<

Make an issue. Or better yet a PR.

# Licence

No. See the [UNLICENCE](./UNLICENSE)

TLDR: This is free and unencumbered software released into the public domain.

# Disclaimer

All registered trademarks or trademarks, copyrights, and intellectual property referenced in this project belong to their respective organizations.

Certain commercial entities, equipment, or materials may be identified in this
project in order to describe an experimental procedure or concept adequately.
Such identification is not intended to imply recommendation or endorsement by this project,
nor is it intended to imply that the  entities, materials, or equipment
are necessarily the best available for the purpose.
