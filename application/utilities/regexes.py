import re

# Regexes built from Figure 6-3. ABNF for Formatted String Binding

alpha_regex = "[A-Za-z]"
digit_regex = r"[0-9]"
escape_regex = r"\\"
punc_regex = r"""(\!|"|#|\$|%|&|'|\(|\)|\+|,|/|\:|;|\<|\=|\>|@|\[|\]|\^|`|\{|\||\}|~)"""  # Second item is DQUOTE
spec1_regex = r"\?"
spec2_regex = r"\*"
spec_chrs_regex = f"(({spec1_regex})+|{spec2_regex})"
special_regex = f"({spec1_regex}|{spec2_regex})"
quoted_regex = f"({escape_regex}({escape_regex}|{special_regex}|{punc_regex}))"  # escape (escape / special / punc)
language_regex = f"{alpha_regex}{{2,3}}"
region_regex = f"({alpha_regex}{{2}}|{digit_regex}{{3}})"  # 2ALPHA / 3DIGIT
langtag_regex = f"{language_regex}(\\-{region_regex})?"  # language ["-" region] ;
logical_regex = r"(\*|\-)"
lang_regex = f"({langtag_regex}|{logical_regex})"  # LANGTAG / logical
unreserved_regex = "[-A-Z._a-z0-9]"  # Optimized from the individual steps; ALPHA / DIGIT / "-" / "." / "_"
avstring_regex = f"""(({spec_chrs_regex}){{,1}}({unreserved_regex}|{quoted_regex})+({spec_chrs_regex}){{,1}}|{logical_regex})"""
part_regex = f"(h|o|a|{logical_regex})"
component_list_regex = rf"(?P<part>{part_regex})\:(?P<vendor>{avstring_regex})\:(?P<product>{avstring_regex})\:(?P<version>{avstring_regex})\:(?P<update>{avstring_regex})\:(?P<edition>{avstring_regex})\:(?P<language>{lang_regex})\:(?P<sw_edition>{avstring_regex})\:(?P<target_sw>{avstring_regex})\:(?P<target_hw>{avstring_regex})\:(?P<other>{avstring_regex})"
cpe23_regex = rf"cpe\:2\.3\:{component_list_regex}"

avstring_compiled_regex = re.compile(f"^{avstring_regex}$")
cpe23_compiled_regex = re.compile(f"^{cpe23_regex}$")
lang_compiled_regex = re.compile(f"^{lang_regex}$")


def is_valid_langtag_regexed_string(string):
    return bool(re.match(lang_compiled_regex, string))


def is_valid_avstring_regexed_string(string):
    return bool(re.match(avstring_compiled_regex, string))


def is_valid_cpe23_regexed_string(string):
    return bool(re.match(cpe23_compiled_regex, string))
