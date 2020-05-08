"""Abstracts license service related functionalities."""

import logging

from typing import Set

import requests
from src.utils import LICENSE_SCORING_URL_REST, post_http_request
from src.v2.models import LicenseAnalysis


logger = logging.getLogger(__file__)  # pylint:disable=C0103


def _extract_conflict_packages(license_service_output):
    """Extract conflict licenses.

    This helper function extracts conflict licenses from the given output
    of license analysis REST service.

    It returns a list of pairs of packages whose licenses are in conflict.
    Note that this information is only available when each component license
    was identified ( i.e. no unknown and no component level conflict ) and
    there was a stack level license conflict.

    :param license_service_output: output of license analysis REST service
    :return: list of pairs of packages whose licenses are in conflict
    """
    license_conflict_packages = []
    if not license_service_output:
        return license_conflict_packages

    conflict_packages = license_service_output.get('conflict_packages', [])
    for conflict_pair in conflict_packages:
        list_pkgs = list(conflict_pair.keys())
        assert len(list_pkgs) == 2
        license_conflict_packages.append(
            {
                "package1": list_pkgs[0],
                "license1": conflict_pair[list_pkgs[0]],
                "package2": list_pkgs[1],
                "license2": conflict_pair[list_pkgs[1]]
            }
        )

    return license_conflict_packages


def _extract_unknown_licenses(license_service_output):
    """Extract unknown licenses.

    This helper function extracts unknown licenses information from the given
    output of license analysis REST service.

    At the moment, there are two types of unknowns:

    a. really unknown licenses: those licenses, which are not understood by our system.
    b. component level conflicting licenses: if a component has multiple licenses
        associated then license analysis service tries to identify a representative
        license for this component. If some licenses are in conflict, then its
        representative license cannot be identified and this is another type of
        'unknown' !

    This function returns both types of unknown licenses.

    :param license_service_output: output of license analysis REST service
    :return: list of packages with unknown licenses and/or conflicting licenses
    """
    # (fixme) reduce cyclomatic complexity
    really_unknown_licenses = []
    lic_conflict_licenses = []
    if not license_service_output:
        return really_unknown_licenses

    # (fixme) refactoring
    if license_service_output.get('status', '') == 'Unknown':
        list_components = license_service_output.get('packages', [])
        for comp in list_components:
            license_analysis = comp.get('license_analysis', {})
            if license_analysis.get('status', '') == 'Unknown':
                pkg = comp.get('package', 'Unknown')
                comp_unknown_licenses = license_analysis.get('unknown_licenses', [])
                for lic in comp_unknown_licenses:
                    really_unknown_licenses.append({
                        'package': pkg,
                        'license': lic
                    })

    # (fixme) refactoring
    if license_service_output.get('status', '') == 'ComponentLicenseConflict':
        list_components = license_service_output.get('packages', [])
        for comp in list_components:
            license_analysis = comp.get('license_analysis', {})
            if license_analysis.get('status', '') == 'Conflict':
                pkg = comp.get('package', 'Unknown')
                dep = {
                    "package": pkg
                }
                comp_conflict_licenses = license_analysis.get('conflict_licenses', [])
                list_conflicting_pairs = []
                for pair in comp_conflict_licenses:
                    assert len(pair) == 2
                    list_conflicting_pairs.append({
                        'license1': pair[0],
                        'license2': pair[1]
                    })
                dep['conflict_licenses'] = list_conflicting_pairs
                lic_conflict_licenses.append(dep)

    output = {
        'unknown': really_unknown_licenses,
        'component_conflict': lic_conflict_licenses
    }
    return output


def _extract_license_outliers(license_service_output):
    """Extract license outliers.

    This helper function extracts license outliers from the given output of
    license analysis REST service.

    :param license_service_output: output of license analysis REST service
    :return: list of license outlier packages
    """
    outliers = []
    if not license_service_output:
        return outliers

    outlier_packages = license_service_output.get('outlier_packages', {})
    for pkg in outlier_packages.keys():
        outliers.append({
            'package': pkg,
            'license': outlier_packages.get(pkg, 'Unknown')
        })

    return outliers


def get_distinct_licenses(normalized_package_details) -> Set[str]:
    """Return list of unique license in the given PackageDetails."""
    licenses = list()
    for _, package_detail in normalized_package_details.items():
        licenses.extend(package_detail.licenses)
    return set(licenses)


def get_license_service_request_payload(normalized_package_details):
    """Prepare payload for license server."""
    license_score_list = []
    for pkg, package_detail in normalized_package_details.items():
        license_score_list.append({
            'package': pkg.name,
            'version': pkg.version,
            'licenses': package_detail.licenses
        })
    return license_score_list


def get_license_analysis_for_stack(
        normalized_package_details) -> LicenseAnalysis:  # pylint:disable=R0914
    """Create LicenseAnalysis from license server."""
    license_url = LICENSE_SCORING_URL_REST + "/api/v1/stack_license"

    # form payload for license service request
    payload = {
        "packages": get_license_service_request_payload(normalized_package_details)
    }
    resp = {}
    flag_stack_license_exception = False
    # (fixme) refactoring
    try:
        resp = post_http_request(url=license_url, payload=payload)
        # lic_response.raise_for_status()  # raise exception for bad http-status codes
        if not resp:
            raise requests.exceptions.RequestException
    except requests.exceptions.RequestException:
        logger.exception("Unexpected error happened while invoking license analysis!")
        flag_stack_license_exception = True

    stack_license = []
    unknown_licenses = []
    license_conflict_packages = []
    license_outliers = []
    if not flag_stack_license_exception:
        # Unused as of now
        # list_components = resp.get('packages', [])
        # for comp in list_components:  # output from license analysis
        #     pkg = Package(name=comp['package'], version=comp['version'])
        #     package_detail = normalized_package_details.get(pkg)
        #     if package_detail:
        #         package_detail.license_analysis = comp.get('license_analysis', {})

        _stack_license = resp.get('stack_license', None)
        if _stack_license is not None:
            stack_license = [_stack_license]
        unknown_licenses = _extract_unknown_licenses(resp)
        license_conflict_packages = _extract_conflict_packages(resp)
        license_outliers = _extract_license_outliers(resp)

    stack_distinct_licenses = list(get_distinct_licenses(normalized_package_details))
    stack_license_conflict = (len(stack_license) == 0 and
                              len(stack_distinct_licenses) > 0)
    return LicenseAnalysis(total_licenses=len(stack_distinct_licenses),
                           distinct_licenses=stack_distinct_licenses,
                           stack_license_conflict=stack_license_conflict,
                           unknown_licenses=unknown_licenses,
                           conflict_packages=license_conflict_packages,
                           outlier_packages=license_outliers)
