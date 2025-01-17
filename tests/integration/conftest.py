import json
import os
from os.path import dirname, realpath

import pytest

dir_path = dirname(realpath(__file__))
top_dir = dirname(dir_path)
test_data_env = os.path.join(top_dir, "data/test_data_env")


@pytest.fixture(autouse=True)
def set_env_vars(monkeysession):
    env_vars = (
        ("NEXTLINUX_TEST_S3_ACCESS_KEY", "9EB92C7W61YPFQ6QLDOU"),
        ("NEXTLINUX_TEST_S3_SECRET_KEY", "TuHo2UbBx+amD3YiCeidy+R3q82MPTPiyd+dlW+s"),
        ("NEXTLINUX_TEST_S3_URL", "http://localhost:9000"),
        ("NEXTLINUX_TEST_S3_BUCKET", "testarchivebucket"),
        ("NEXTLINUX_TEST_SWIFT_AUTH_URL", "http://localhost:8080/auth/v1.0"),
        ("NEXTLINUX_TEST_SWIFT_KEY", "testing"),
        ("NEXTLINUX_TEST_SWIFT_USER", "test:tester"),
        ("NEXTLINUX_TEST_SWIFT_CONTAINER", "testarchive"),
        (
            "NEXTLINUX_TEST_DB_URL",
            "postgresql://postgres:postgres@localhost:5432/postgres",
        ),
        ("NEXTLINUX_TEST_DB_USER", "postgres"),
        ("NEXTLINUX_TEST_DB_PASS", "postgres"),
        ("NEXTLINUX_TEST_DATA_ENV_DIR", test_data_env),
    )
    for environ, value in env_vars:
        monkeysession.setenv(environ, value)


@pytest.fixture
def test_data_path():
    return os.path.join(top_dir, "data")


@pytest.fixture
def bundle():
    def find(bundle_name="bundle-large_whitelist.json"):
        data_dir = os.path.join(top_dir, "data")
        bundle_path = os.path.join(data_dir, bundle_name)
        with open(bundle_path) as f:
            return json.load(f)

    return find


@pytest.fixture(autouse=True)
def set_legacy_provider(monkeysession):
    def _provider_name(section):
        return "legacy"

    monkeysession.setattr(
        "nextlinux_engine.services.policy_engine.engine.vulns.providers.get_provider_name",
        _provider_name,
    )
