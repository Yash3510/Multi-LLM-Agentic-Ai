import import_scan

DISTS = {"pydantic": ["pydantic"], "gplthing": ["gpl-thing"], "fitz": ["PyMuPDF"]}
LICENCES = {"pydantic": "MIT", "gpl-thing": "GPL-3.0-only", "pymupdf": "AGPL-3.0-or-later"}
PDF_ADAPTER = "core/knowledge/src/fource/knowledge/pdf/"


def scan(files: dict[str, str], commercial_paths: dict[str, tuple[str, ...]] | None = None):
    return import_scan.check_imports(files, DISTS, LICENCES, commercial_paths or {})


def test_top_level_names_of_absolute_imports() -> None:
    source = "import a.b, c\nfrom d.e import f\nfrom . import g\nfrom .h import i\n"
    assert import_scan.imported_modules(source) == {"a", "c", "d"}


def test_permissive_standard_library_and_own_imports_pass() -> None:
    source = "import json\nimport pydantic\nfrom fource.common import Settings\n"
    assert scan({"core/x/src/fource/x/a.py": source}) == []


def test_copyleft_imports_fail() -> None:
    problems = scan({"core/x/src/fource/x/a.py": "import gplthing\n"})
    assert problems == [
        "core/x/src/fource/x/a.py: imports gplthing from gpl-thing (GPL-3.0-only), "
        "a copyleft library 4CE has no commercial licence for"
    ]


def test_a_commercial_library_only_where_its_adapter_lives() -> None:
    paths = {"pymupdf": (PDF_ADAPTER,)}
    assert scan({f"{PDF_ADAPTER}pymupdf_adapter.py": "import fitz\n"}, paths) == []
    problems = scan({"core/reading/src/fource/reading/boxes.py": "import fitz\n"}, paths)
    assert len(problems) == 1 and "only in" in problems[0]


def test_unknown_imports_fail_closed() -> None:
    problems = scan({"core/x/src/fource/x/a.py": "import mystery\n"})
    assert problems and "no installed package" in problems[0]


def test_a_package_missing_from_the_sbom_fails_closed() -> None:
    dists = DISTS | {"stray": ["stray-lib"]}
    problems = import_scan.check_imports(
        {"core/x/src/fource/x/a.py": "import stray\n"}, dists, LICENCES, {}
    )
    assert problems and "stray-lib" in problems[0] and "not in the SBOM" in problems[0]
