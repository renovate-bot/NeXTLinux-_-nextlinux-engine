import pytest

from nextlinux_engine.services.policy_engine.engine.vulns.scanners import GovulnersScanner


@pytest.mark.parametrize(
    "input, expected_output",
    [
        ("nvd", True),
        ("nvdv2", True),
        (["nvdv2:cves"], True),
        ("", False),
        (["nvd", "test"], False),
        (["test"], False),
    ],
)
def test_is_only_nvd_namespace(input, expected_output):
    """
    Tests private function in GovulnersScanner that determines if namespace is an nvd namespace
    """
    assert GovulnersScanner()._is_only_nvd_namespace(input) is expected_output
