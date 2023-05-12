from nextlinux_engine.analyzers.gosbom.handlers.common import save_entry_to_findings
from nextlinux_engine.analyzers.utils import dig


def save_entry(findings, engine_entry, pkg_key=None):
    if not pkg_key:
        pkg_key = engine_entry.get("name", "")

    save_entry_to_findings(findings, engine_entry, "pkgs.allinfo", pkg_key)


def translate_and_save_entry(findings, artifact):
    """
    Handler function to map gosbom results for an debian package type into the engine "raw" document format.
    """
    _all_package_files(findings, artifact)
    _all_packages(findings, artifact)
    _all_packages_plus_source(findings, artifact)
    _all_package_info(findings, artifact)


def _all_package_info(findings, artifact):
    name = artifact["name"]
    version = artifact["version"]
    release = dig(artifact, "metadata", "release")

    if release:
        version = artifact["version"] + "-" + release

    maintainer = dig(artifact, "metadata", "maintainer")
    if maintainer:
        maintainer += " (maintainer)"

    size = dig(artifact, "metadata", "installedSize")
    if size:
        # convert KB to Bytes
        size = size * 1000
    else:
        size = "N/A"

    license = dig(artifact, "licenses")
    if license:
        license = " ".join(license)
    else:
        license = "Unknown"

    pkg_value = {
        "version": version,
        "sourcepkg": dig(artifact, "metadata", "source", force_default="N/A"),
        "arch": dig(artifact, "metadata", "architecture", force_default="N/A"),
        "origin": maintainer or "N/A",
        "release": "N/A",
        "size": str(size),
        "license": license,
        "type": "dpkg",
        "cpes": artifact.get("cpes", []),
    }

    save_entry(findings, pkg_value, name)


def _all_packages_plus_source(findings, artifact):
    name = artifact["name"]
    version = artifact["version"]

    origin_package = dig(artifact, "metadata", "originPackage")

    findings["package_list"]["pkgs_plus_source.all"]["base"][name] = version
    if origin_package:
        findings["package_list"]["pkgs_plus_source.all"]["base"][
            origin_package] = version


def _all_packages(findings, artifact):
    name = artifact["name"]
    version = artifact["version"]
    if name and version:
        findings["package_list"]["pkgs.all"]["base"][name] = version


def _all_package_files(findings, artifact):
    for file in dig(artifact, "metadata", "files", force_default=[]):
        original_path = file.get("path")
        if not original_path.startswith("/"):
            # the 'alpine-baselayout' package is installed relative to root,
            # however, gosbom reports this as an absolute path
            original_path = "/" + original_path

        # nextlinux-engine considers all parent paths to also be a registered apkg path (except root)
        findings["package_list"]["pkgfiles.all"]["base"][
            original_path] = "DPKGFILE"