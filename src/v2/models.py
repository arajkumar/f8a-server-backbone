# generated by datamodel-codegen:
#   filename:  v2.yaml
#   timestamp: 2020-04-25T19:10:47+00:00

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class Ecosystem(str, Enum):
    maven = 'maven'
    pypi = 'pypi'
    npm = 'npm'


class Severity(str, Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    critical = 'critical'


class BasicVulnerabilityFields(BaseModel):
    cve_ids: Optional[List[str]] = None
    cvss: float
    cwes: Optional[List[str]] = None
    cvss_v3: str
    severity: 'Severity'
    title: str
    id: str
    url: str


class Exploit(str, Enum):
    High = 'High'
    Functional = 'Functional'
    Proof_of_Concept = 'Proof of Concept'
    Unproven = 'Unproven'
    Not_Defined = 'Not Defined'


class Reference(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None


class PremiumVulnerabilityFields(BasicVulnerabilityFields):
    malicious: Optional[bool] = True
    patch_exists: Optional[bool] = False
    fixable: Optional[bool] = False
    exploit: Optional['Exploit'] = None
    description: Optional[str] = None
    fixed_in: Optional[List[str]] = None
    references: Optional[List['Reference']] = None


class Package(BaseModel):
    name: str
    version: str
    dependencies: Optional[List['Package']] = []


class ComponentConflictItem(BaseModel):
    license1: Optional[str] = None
    license2: Optional[str] = None


class ReallyUnknownItem(BaseModel):
    package: Optional[str] = None
    license: Optional[str] = None


class UnknownLicenses(BaseModel):
    component_conflict: Optional[List['ComponentConflictItem']] = None
    really_unknown: Optional[List['ReallyUnknownItem']] = None


class ConflictPackages(BaseModel):
    package1: str
    license1: str
    package2: str
    license2: str


class LicenseAnalysis(BaseModel):
    outlier_packages: List[Dict[str, Any]] = None
    conflict_packages: List['ConflictPackages'] = None
    current_stack_license: Dict[str, Any] = None
    unknown_licenses: 'UnknownLicenses' = None
    distinct_licenses: Optional[List[str]] = None
    stack_license_conflict: Optional[bool] = None
    total_licenses: Optional[int] = None


class UsedByItem(BaseModel):
    name: Optional[str] = None
    stars: Optional[int] = None


class GitHubDetails(BaseModel):
    watchers: Optional[int] = None
    first_release_date: Optional[str] = None
    total_releases: Optional[int] = None
    issues: Optional[Dict[str, Any]] = None
    pull_requests: Optional[Dict[str, Any]] = None
    dependent_repos: Optional[int] = None
    open_issues_count: Optional[int] = None
    latest_release_duration: Optional[str] = None
    forks_count: Optional[int] = None
    contributors: Optional[int] = None
    size: Optional[str] = None
    stargazers_count: Optional[int] = None
    used_by: Optional[List[UsedByItem]] = None
    dependent_projects: Optional[int] = None


class PackageDetails(Package):
    latest_version: str
    github: Optional['GitHubDetails'] = None
    licenses: Optional[List[str]] = None
    ecosystem: 'Ecosystem'
    url: Optional[str] = None


class PackageDetailsForRegisteredUser(PackageDetails):
    public_vulnerabilities: Optional[List['PremiumVulnerabilityFields']] = Field(
        None, description='Publicly known vulnerability details'
    )
    private_vulnerabilities: Optional[List['PremiumVulnerabilityFields']] = Field(
        None,
        description='Private vulnerability details, available only to registered\nusers\n',
    )
    recommended_version: Optional[str] = Field(
        None,
        description='Recommended package version which includes fix for both public and private vulnerabilities.\n',
    )
    vulnerable_dependencies: Optional[List['PackageDetailsForRegisteredUser']] = Field(
        None, description='List of dependencies which are vulnerable.\n'
    )


class PackageDetailsForFreeTier(PackageDetails):
    public_vulnerabilities: Optional[List['BasicVulnerabilityFields']] = Field(
        None, description='Publicly known vulnerability details'
    )
    private_vulnerabilities: Optional[List['BasicVulnerabilityFields']] = Field(
        None, description='Private vulnerability details with limited info'
    )
    recommended_version: Optional[str] = Field(
        None,
        description='Recommended package version which includes fix for public vulnerabilities.\n',
    )
    vulnerable_dependencies: Optional[List['PackageDetailsForFreeTier']] = Field(
        None, description='List of dependencies which are vulnerable.\n'
    )


class RecommendedPackageData(PackageDetails):
    confidence_reason: Optional[float] = None
    reason: Optional[str] = None
    topic_list: Optional[List[str]] = None


class RegistrationStatus(str,Enum):
    registered = 'registered'
    freetier = 'freetier'


class RecommendationStatus(str, Enum):
    success = 'success'
    pgm_error = 'pgm_error'


class Audit(BaseModel):
    started_at: str
    ended_at: str
    version: str


class StackAggregatorResult(BaseModel):
    _audit: Optional['Audit'] = None
    uuid: Optional[UUID] = None
    external_request_id: Optional[str] = None
    registration_status: Optional['RegistrationStatus'] = None
    manifest_file_path: Optional[str] = None
    manifest_name: Optional[str] = None
    ecosystem: Optional['Ecosystem'] = None
    unknown_dependencies: Optional[List['Package']] = None
    license_analysis: Optional['LicenseAnalysis'] = None


class StackAggregatorResultForRegisteredUser(StackAggregatorResult):
    analyzed_dependencies: Optional[List['PackageDetailsForRegisteredUser']] = Field(
        None,
        description="All direct dependencies details regardless of it's vulnerability status\n",
    )


class StackAggregatorResultForFreeTier(StackAggregatorResult):
    registration_link: str
    analyzed_dependencies: Optional[List['PackageDetailsForFreeTier']] = Field(
        None,
        description="All direct dependencies details regardless of it's vulnerability status\n",
    )


class StackAggregatorRequest(BaseModel):
    registration_status: 'RegistrationStatus' = 'freetier'
    uuid: UUID = None
    external_request_id: str
    show_transitive: Optional[bool] = Field(
        True,
        description='This is required to enable or disable the transitive support\n',
    )
    ecosystem: 'Ecosystem'
    manifest_file: str
    manifest_file_path: str
    packages: List['Package']

    @validator('ecosystem')
    def normalize_ecosystem(cls, ecosystem):
        return ecosystem.value.lower()


class StackRecommendationResult(BaseModel):
    _audit: 'Audit'
    uuid: UUID
    external_request_id: str
    registration_status: 'RegistrationStatus'
    recommendation_status: 'RecommendationStatus'
    companion: List['RecommendedPackageData']
    manifest_file_path: str
    usage_outliers: List[Dict[str, Any]]


class RecommenderRequest(StackAggregatorRequest):
    pass


Package.update_forward_refs()
PackageDetailsForRegisteredUser.update_forward_refs()
PackageDetailsForFreeTier.update_forward_refs()
