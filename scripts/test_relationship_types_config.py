#!/usr/bin/env python3
"""Test the .mif/config.yaml relationship_types registry (SPECIFICATION.md
8.1/8.3), implemented in okf_validate.py.

Regression coverage for #232: SPECIFICATION.md documented a structured
custom-relationship-type registry with no corresponding implementation
anywhere in this repo. Covers:

- a bundle with .mif/config.yaml declaring a custom type, used correctly ->
  passes;
- the same, but the document uses an undeclared custom type -> a clear error
  naming the undeclared type, not a crash;
- a bundle with NO .mif/config.yaml, using an arbitrary namespaced type ->
  stays lenient (today's pre-#232 behavior, unchanged -- this feature is
  opt-in, not a retroactive tightening);
- a malformed .mif/config.yaml (wrong casing on name/namespace) -> a clear
  structural error, not a crash, and concepts in that bundle aren't
  processed against a registry that failed to load;
- a declared type's relationship metadata values are checked against that
  type's declared properties[] (type/enum/range), not just checked for
  existence -- an in-range/in-enum value passes, an out-of-range/not-in-enum
  value produces a clear error naming the property and value.

Also exercises the body-markdown-link regex fix this feature required:
REL_LINE_RE previously had no way to match a namespaced type token at all
(no ":" in its character class), so ANY concept using a custom relationship
type would unconditionally fail the pre-existing frontmatter<->body sync
check (3), regardless of whether the type was declared. The `declared` and
`no_config` fixtures both include a body "## Relationships" mirror line for
their namespaced relationship, so a regression in that regex shows up here
as a spurious "relationships out of sync" error.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import okf_validate  # noqa: E402  (local module, path set above)

FIXTURES = ROOT / "test" / "relationship_types"


def check_declared_custom_type_passes() -> list[str]:
    errors, _warnings, count = okf_validate.validate_bundle(FIXTURES / "declared")
    problems = []
    if count != 2:
        problems.append(f"expected 2 concepts, got {count}")
    if errors:
        problems.append(f"expected no errors, got: {errors}")
    return problems


def check_undeclared_custom_type_fails_clearly() -> list[str]:
    errors, _warnings, count = okf_validate.validate_bundle(FIXTURES / "undeclared")
    problems = []
    if count != 1:
        problems.append(f"expected 1 concept, got {count}")
    matching = [e for e in errors if "farm:undeclared-type" in e and "not declared" in e]
    if len(matching) != 1:
        problems.append(f"expected exactly 1 clear 'not declared' error, got: {errors}")
    return problems


def check_no_config_stays_lenient() -> list[str]:
    errors, _warnings, count = okf_validate.validate_bundle(FIXTURES / "no_config")
    problems = []
    if count != 1:
        problems.append(f"expected 1 concept, got {count}")
    if errors:
        problems.append(f"bundle with no .mif/config.yaml must stay lenient, got errors: {errors}")
    return problems


def check_malformed_config_reports_structural_errors() -> list[str]:
    errors, _warnings, count = okf_validate.validate_bundle(FIXTURES / "malformed_config")
    problems = []
    if count != 1:
        problems.append(f"expected 1 concept, got {count}")
    if not any(".name:" in e and "lowercase-invalid" in e for e in errors):
        problems.append(f"expected a 'name' pattern error naming the bad value, got: {errors}")
    if not any(".namespace:" in e and "FARM" in e for e in errors):
        problems.append(f"expected a 'namespace' pattern error naming the bad value, got: {errors}")
    # The fixture's one concept uses a namespaced type (farm:whatever) that
    # isn't declared anywhere -- if check (7) ran against a registry built
    # from an invalid config, it would (wrongly) flag this too. It must not:
    # a config that fails to load disables check (7) entirely for the bundle.
    if any("not declared" in e for e in errors):
        problems.append(f"check (7) must not run against an invalid config, got: {errors}")
    return problems


def check_kebab_case_mapping_matches_spec_example() -> list[str]:
    """SPECIFICATION.md 8.1's own example: name: BreedsWith, namespace: farm
    -> relationships[].type value "farm:breeds-with"."""
    config = {"relationship_types": [{"name": "BreedsWith", "namespace": "farm"}]}
    registry, errors = okf_validate._custom_relationship_type_registry(config)
    if "farm:breeds-with" not in registry:
        return [f"expected 'farm:breeds-with' in registry, got keys: {list(registry.keys())}"]
    if errors:
        return [f"expected no errors for a single declaration, got: {errors}"]
    return []


def check_duplicate_declaration_reports_an_error() -> list[str]:
    """A namespace+name declared twice must not silently let the second
    entry overwrite the first with no diagnostic."""
    config = {
        "relationship_types": [
            {"name": "BreedsWith", "namespace": "farm", "symmetric": False},
            {"name": "BreedsWith", "namespace": "farm", "symmetric": True},
        ]
    }
    registry, errors = okf_validate._custom_relationship_type_registry(config)
    if "farm:breeds-with" not in registry:
        return [f"expected 'farm:breeds-with' still in registry, got keys: {list(registry.keys())}"]
    if not any("more than once" in e for e in errors):
        return [f"expected a duplicate-declaration error, got: {errors}"]
    return []


def check_namespaced_kebab_survives_colon() -> list[str]:
    """_kebab('farm:BreedsWith') must not grow a spurious hyphen right after
    the colon -- a namespace prefix is a word boundary, same as the start of
    the string."""
    result = okf_validate._kebab("farm:BreedsWith")
    if result != "farm:breeds-with":
        return [f"expected 'farm:breeds-with', got {result!r}"]
    return []


def check_property_value_constraints_enforced_end_to_end() -> list[str]:
    """SPECIFICATION.md 8.3's own worked example (enum: [direct, indirect,
    partial], range: [0.0, 1.0]) via the full validate_bundle() pipeline: an
    in-range/in-enum relationship passes, an out-of-range/not-in-enum one
    produces a clear per-property error."""
    errors, _warnings, count = okf_validate.validate_bundle(FIXTURES / "property_values")
    problems = []
    if count != 2:
        problems.append(f"expected 2 concepts, got {count}")
    # "invalid.md" contains "valid.md" as a substring -- match on the leading
    # path segment so the two fixtures' errors aren't cross-counted.
    valid_errors = [e for e in errors if e.startswith("test/relationship_types/property_values/valid.md")]
    if valid_errors:
        problems.append(f"expected no errors for valid.md, got: {valid_errors}")
    invalid_errors = [e for e in errors if e.startswith("test/relationship_types/property_values/invalid.md")]
    if not any("not one of the declared enum values" in e for e in invalid_errors):
        problems.append(f"expected an enum violation for invalid.md, got: {invalid_errors}")
    if not any("outside the declared range" in e for e in invalid_errors):
        problems.append(f"expected a range violation for invalid.md, got: {invalid_errors}")
    return problems


def check_property_type_mismatch_detected() -> list[str]:
    entry = {"namespace": "farm", "properties": [{"name": "success", "type": "boolean"}]}
    errs = okf_validate._relationship_metadata_errors(entry, {"farm:success": "yes"})
    if not any("expected type 'boolean'" in e for e in errs):
        return [f"expected a type-mismatch error, got: {errs}"]
    return []


def check_range_on_a_string_property_does_not_crash() -> list[str]:
    """`range` only applies to type: integer/decimal (schema's own field
    description); a misdeclared `range` on a type: string property must not
    reach `lo <= value <= hi` with a non-numeric value and raise TypeError --
    it must be silently ignored (the same as any other inapplicable
    constraint), never a crash in a required CI gate."""
    entry = {"namespace": "farm", "properties": [{"name": "label", "type": "string", "range": [0, 1]}]}
    errs = okf_validate._relationship_metadata_errors(entry, {"farm:label": "hello"})
    if errs:
        return [f"expected no errors (range is inapplicable to type:string, not a crash), got: {errs}"]
    return []


def check_declared_property_absent_from_metadata_is_not_an_error() -> list[str]:
    """A declared property is only checked when the relationship's metadata
    actually carries it -- properties are optional-when-present, not
    required-if-declared."""
    entry = {
        "namespace": "farm",
        "properties": [{"name": "severity", "type": "decimal", "range": [0.0, 1.0]}],
    }
    errs = okf_validate._relationship_metadata_errors(entry, {})
    if errs:
        return [f"expected no errors when the property is simply absent, got: {errs}"]
    return []


CHECKS = [
    ("declared custom relationship type passes (#232)", check_declared_custom_type_passes),
    ("undeclared custom relationship type fails with a clear error (#232)", check_undeclared_custom_type_fails_clearly),
    ("bundle with no .mif/config.yaml stays lenient (#232)", check_no_config_stays_lenient),
    ("malformed .mif/config.yaml reports structural errors, not a crash (#232)", check_malformed_config_reports_structural_errors),
    ("PascalCase name kebab-cases to match SPECIFICATION.md 8.1's own example", check_kebab_case_mapping_matches_spec_example),
    ("duplicate namespace+name declaration reports an error, not a silent overwrite", check_duplicate_declaration_reports_an_error),
    ("_kebab() doesn't grow a spurious hyphen after a namespace colon", check_namespaced_kebab_survives_colon),
    ("declared property enum/range constraints enforced end-to-end (#232 follow-up)", check_property_value_constraints_enforced_end_to_end),
    ("declared property type mismatch is detected", check_property_type_mismatch_detected),
    ("a declared property absent from metadata is not an error", check_declared_property_absent_from_metadata_is_not_an_error),
    ("range on a type:string property is ignored, not a crash", check_range_on_a_string_property_does_not_crash),
]


def main() -> int:
    failed = []
    for label, check in CHECKS:
        problems = check()
        if problems:
            failed.append(label)
            print(f"FAIL: {label}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"PASS: {label}")
    if failed:
        print(f"\nrelationship_types config test FAILED: {failed}")
        return 1
    print("\nAll relationship_types config tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
