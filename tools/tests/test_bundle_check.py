from pathlib import Path

import licence_gate

PG = "postgres:18.6-alpine@sha256:77f5"
PROM = "prom/prometheus:v3.15.0@sha256:efd7"


def complete(image: str) -> dict[str, str]:
    return {"LICENSE": "text", "NOTICE": "text", "VERSION": f"{image}\nupstream\n", "SOURCE": "url"}


def test_a_complete_bundle_passes() -> None:
    services = {"postgres": {"image": PG}, "prometheus": {"image": PROM}}
    bundle = {"postgres": complete(PG), "prometheus": complete(PROM)}
    assert licence_gate.check_bundle(services, bundle) == []


def test_component_names_come_from_the_image() -> None:
    assert licence_gate.component(PROM) == "prometheus"
    assert licence_gate.component("ghcr.io/org/minio:RELEASE.1") == "minio"
    assert licence_gate.component(PG) == "postgres"


def test_missing_folders_and_files_fail() -> None:
    services = {"postgres": {"image": PG}, "prometheus": {"image": PROM}}
    partial = complete(PG)
    del partial["NOTICE"]
    problems = licence_gate.check_bundle(services, {"postgres": partial})
    assert any("postgres" in p and "NOTICE" in p for p in problems)
    assert any("prometheus" in p and "no deploy/third-party/prometheus" in p for p in problems)


def test_version_must_name_the_image_in_use() -> None:
    services = {"postgres": {"image": PG}}
    old = complete("postgres:17.0-alpine@sha256:aaaa")
    problems = licence_gate.check_bundle(services, {"postgres": old})
    assert problems and "VERSION" in problems[0]


def test_pulled_images_are_pinned_by_digest_and_built_ones_need_not_be() -> None:
    services = {
        "postgres": {"image": "postgres:18.6-alpine"},
        "minio": {"image": "fource/minio:RELEASE.1", "build": {"context": "."}},
    }
    bundle = {
        "postgres": complete("postgres:18.6-alpine"),
        "minio": complete("fource/minio:RELEASE.1"),
    }
    problems = licence_gate.check_bundle(services, bundle)
    assert problems == ["postgres: image postgres:18.6-alpine is not pinned by digest"]


def test_bundle_folders_no_service_uses_are_flagged() -> None:
    problems = licence_gate.check_bundle({}, {"redis": complete("redis:8")})
    assert problems == ["deploy/third-party/redis: no compose service uses it"]


def test_a_service_without_an_image_name_fails() -> None:
    problems = licence_gate.check_bundle({"cache": {"build": {"context": "."}}}, {})
    assert problems == ["cache: has no image name, so its bundle folder cannot be found"]


def test_registry_hosts_with_a_port_are_not_the_component() -> None:
    assert licence_gate.component("localhost:5000/minio:RELEASE.1@sha256:ab") == "minio"


MINIO = "fource/minio:RELEASE.1"
COMMIT = "9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a"
DOCKERFILE = f"FROM x\nARG MINIO_RELEASE=RELEASE.1\nARG MINIO_COMMIT={COMMIT}\n"


def test_a_built_service_records_its_upstream_commit_in_source() -> None:
    services = {"minio": {"image": MINIO, "build": {"context": "."}}}
    recorded = complete(MINIO) | {"SOURCE": f"https://example/tree/RELEASE.1\ncommit {COMMIT}\n"}
    assert licence_gate.check_bundle(services, {"minio": recorded}, {"minio": DOCKERFILE}) == []
    stale = complete(MINIO) | {"SOURCE": "commit 0000000000000000000000000000000000000000\n"}
    problems = licence_gate.check_bundle(services, {"minio": stale}, {"minio": DOCKERFILE})
    assert problems and "SOURCE" in problems[0] and COMMIT[:8] in problems[0]
    unpinned = licence_gate.check_bundle(services, {"minio": recorded}, {"minio": "FROM x\n"})
    assert unpinned and "_COMMIT" in unpinned[0]


def test_both_compose_file_extensions_are_read(tmp_path: Path) -> None:
    (tmp_path / "core.yml").write_text("services:\n  a:\n    image: a:1\n", encoding="utf-8")
    (tmp_path / "addon.yaml").write_text("services:\n  b:\n    image: b:1\n", encoding="utf-8")
    assert sorted(licence_gate.compose_services(tmp_path)) == ["a", "b"]
