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
