import re

from .regexes import cpe23_compiled_regex


def cpe23_to_cpe22(cpe23: str) -> str:
    """
    Convert a CPE 2.3 formatted string to a CPE 2.2 URI.

    Example:
        cpe:2.3:a:3com:3cdaemon:-:*:*:*:*:*:*:*
        ->
        cpe:/a:3com:3cdaemon

    Args:
        cpe23: A CPE 2.3 formatted string.

    Returns:
        The equivalent CPE 2.2 URI string.

    Raises:
        ValueError: If the input is not a valid CPE 2.3 string.
    """
    prefix = "cpe:2.3:"

    if not cpe23.startswith(prefix):
        raise ValueError(f"Not a CPE 2.3 formatted string: {cpe23!r}")

    # We need to preformat escaped colons \: so the split works
    cpe23 = cpe23.replace("\\:", "%5c%3a")

    parts = cpe23[len(prefix) :].split(":")

    if len(parts) != 11:
        raise ValueError(f"Expected 11 CPE 2.3 components, got {len(parts)}: {cpe23}")

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
    ) = parts

    # CPE 2.2 only has:
    # part:vendor:product:version:update:edition:language
    #
    # The following CPE 2.3 attributes have no direct CPE 2.2
    # representation:
    #   sw_edition
    #   target_sw
    #   target_hw
    #   other
    #
    # Edition may need special handling for CPE 2.3's packed edition
    # syntax.

    def unescape(value: str) -> str:
        """Convert CPE 2.3 escaping to CPE 2.2 URI escaping."""
        if value in ("*", "-"):
            return value

        # CPE 2.3 escaping uses backslash for special characters.
        # Decode escaped characters first.
        value = re.sub(r"\\([\\:!*?])", r"\1", value)

        # CPE 2.2 URI escaping.
        value = value.replace("%", "%25")
        value = value.replace(" ", "%20")
        value = value.replace(":", "%3a")
        value = value.replace("/", "%2f")
        value = value.replace("\\", "%5c")
        value = value.replace("?", "%3f")
        value = value.replace("#", "%23")

        return value

    converted = [
        unescape(part),
        unescape(vendor),
        unescape(product),
        unescape(version),
        unescape(update),
        unescape(edition),
        unescape(language),
    ]

    # CPE 2.2 URIs traditionally omit trailing wildcard/undefined attributes.
    while converted and converted[-1] in ("*", "-"):
        converted.pop()

    return "cpe:/" + ":".join(converted)


def cpe23_formatted_string_to_wfn(
    formatted_string: str,
) -> tuple[str, str, str, str, str, str, str, str, str, str, str]:
    match = cpe23_compiled_regex.match(formatted_string)
    if not match:
        raise ValueError(f"Invalid CPE23 formated string: {formatted_string}")
    return (
        match.group("part"),
        match.group("vendor"),
        match.group("product"),
        match.group("version"),
        match.group("update"),
        match.group("edition"),
        match.group("language"),
        match.group("sw_edition"),
        match.group("target_sw"),
        match.group("target_hw"),
        match.group("other"),
    )


# CPE logical values as represented by the formatted-string binding.
ANY = "*"
NA = "-"
