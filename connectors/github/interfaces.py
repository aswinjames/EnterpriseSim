"""Public GitHub Connector — abstract interfaces (DESIGN ONLY, no implementation).

Ingests PUBLIC GitHub repositories and extracts **engineering metadata only**, normalizing
it into EnterpriseSim ECL objects (KnowledgeObject / ContextObject / ExperienceObject).

Compliance boundary (see README.md):
  * Metadata and structure only — never source code text, issue/PR bodies verbatim, or any
    other potentially-copyrightable content. No proprietary content is copied.
  * Public repositories only; respect GitHub Terms of Service, rate limits and robots.
  * Provenance (source repo + license + commit SHA) travels with every normalized object.

Every method body is elided (``...``). Implementations live outside this repository; this is
the contract a connector implementation fulfils.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence


# ---------------------------------------------------------------------------
# Extracted metadata value types (facts only — no content bodies)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RepoMetadata:
    """Repository-level facts. No file contents."""
    full_name: str                 # "owner/repo"
    description: str               # short public description (fact, not content corpus)
    primary_language: str
    languages: Mapping[str, int]   # language -> byte count (a GitHub API fact)
    topics: Sequence[str]
    license_spdx: str              # e.g. "Apache-2.0"; drives compliance handling
    default_branch: str
    stars: int
    forks: int
    created_at: str
    pushed_at: str


@dataclass(frozen=True)
class ReleaseMetadata:
    tag: str
    name: str
    published_at: str
    is_prerelease: bool
    asset_count: int
    # NOTE: release notes bodies are summarized to structured facts, not stored verbatim.


@dataclass(frozen=True)
class PRMetadata:
    number: int
    state: str                     # open | closed | merged
    created_at: str
    merged_at: str | None
    changed_files: int
    additions: int
    deletions: int
    commit_count: int
    review_count: int
    labels: Sequence[str]
    linked_issue_count: int
    # title is kept as a short fact; body text is NOT stored verbatim.


@dataclass(frozen=True)
class CommitMetadata:
    sha: str
    authored_at: str
    files_changed: int
    additions: int
    deletions: int
    # message is reduced to a structured summary (type, scope) — not stored verbatim.
    conventional_type: str | None  # feat | fix | chore | ... if parseable


@dataclass(frozen=True)
class LabelMetadata:
    name: str
    usage_count: int


@dataclass(frozen=True)
class FileRelationship:
    """A dependency/relationship fact derived from manifests — not file contents."""
    kind: str                      # depends_on | imported_by | test_of | workflow_for
    from_path: str
    to_ref: str                    # a module/package/path reference (structure, not content)


@dataclass(frozen=True)
class WorkflowMetadata:
    """CI/CD workflow structure (stages/triggers), not the YAML verbatim."""
    name: str
    triggers: Sequence[str]        # push | pull_request | schedule | ...
    jobs: Sequence[str]            # job names / stage names
    uses_matrix: bool


@dataclass(frozen=True)
class TestMetadata:
    """Test-suite facts derived from CI output / structure, not test source."""
    framework: str | None
    test_file_count: int
    reported_coverage: float | None
    suites: Sequence[str]


@dataclass(frozen=True)
class RepoSnapshot:
    """The complete extracted metadata for one repository at one point in time."""
    repo: RepoMetadata
    releases: Sequence[ReleaseMetadata] = field(default_factory=tuple)
    pull_requests: Sequence[PRMetadata] = field(default_factory=tuple)
    commits: Sequence[CommitMetadata] = field(default_factory=tuple)
    labels: Sequence[LabelMetadata] = field(default_factory=tuple)
    file_relationships: Sequence[FileRelationship] = field(default_factory=tuple)
    workflows: Sequence[WorkflowMetadata] = field(default_factory=tuple)
    tests: Sequence[TestMetadata] = field(default_factory=tuple)


@dataclass(frozen=True)
class NormalizationResult:
    """ECL objects produced from a snapshot. IDs are namespaced to the connector source."""
    knowledge_objects: Sequence[Mapping[str, object]]    # KnowledgeObject dicts (KN-###)
    context_objects: Sequence[Mapping[str, object]]      # ContextObject dicts (CTX-###)
    experience_objects: Sequence[Mapping[str, object]]   # ExperienceObject dicts (EXP-###)
    provenance: Mapping[str, object]                     # source repo, license, fetched_at


# ---------------------------------------------------------------------------
# Rate limiting / compliance
# ---------------------------------------------------------------------------

class ComplianceGuard(Protocol):
    """Enforces the metadata-only, public-only, ToS-respecting boundary."""

    def is_public(self, full_name: str) -> bool: ...
    def license_allows_metadata_extraction(self, spdx: str) -> bool: ...
    def redact_content(self, text: str) -> str:
        """Reduce any free text to structured facts; never return verbatim content."""
        ...


class RateLimiter(Protocol):
    def acquire(self, cost: int = 1) -> None: ...
    def remaining(self) -> int: ...


# ---------------------------------------------------------------------------
# The four designed components
# ---------------------------------------------------------------------------

class GitHubConnector(ABC):
    """Authenticated, rate-limited entry point to the public GitHub API."""

    @abstractmethod
    def authenticate(self, token: str | None) -> None:
        """Authenticate (optional token for higher rate limits); public data only."""
        ...

    @abstractmethod
    def list_public_repositories(self, query: str, limit: int) -> Sequence[str]:
        """Return `owner/repo` names matching a search query, public repositories only."""
        ...

    @abstractmethod
    def rate_limiter(self) -> RateLimiter: ...

    @abstractmethod
    def compliance(self) -> ComplianceGuard: ...


class RepositoryScanner(ABC):
    """Enumerates the artifacts of one repository via the connector."""

    @abstractmethod
    def scan(self, full_name: str, connector: GitHubConnector) -> RepoSnapshot:
        """Enumerate repo metadata, releases, PRs, commits, labels, workflows, tests."""
        ...

    @abstractmethod
    def since(self, full_name: str, connector: GitHubConnector, watermark: str) -> RepoSnapshot:
        """Incremental scan of artifacts changed since a watermark timestamp/SHA."""
        ...


class ArtifactExtractor(ABC):
    """Extracts structured, content-free metadata from a raw scan."""

    @abstractmethod
    def extract(self, snapshot: RepoSnapshot, guard: ComplianceGuard) -> RepoSnapshot:
        """Return a snapshot with all free-text reduced to facts (content redacted)."""
        ...

    @abstractmethod
    def derive_file_relationships(self, full_name: str, connector: GitHubConnector) -> Sequence[FileRelationship]:
        """Derive dependency/test/workflow relationships from manifests — structure only."""
        ...


class EnterpriseNormalizer(ABC):
    """Maps extracted metadata into EnterpriseSim ECL objects."""

    @abstractmethod
    def to_knowledge(self, snapshot: RepoSnapshot) -> Sequence[Mapping[str, object]]:
        """Repository/architecture/CI facts -> KnowledgeObject dicts (validate vs schema)."""
        ...

    @abstractmethod
    def to_context(self, snapshot: RepoSnapshot, task_ref: str) -> Mapping[str, object]:
        """A scan/analysis task working set -> a ContextObject dict."""
        ...

    @abstractmethod
    def to_experience(self, snapshots: Sequence[RepoSnapshot]) -> Sequence[Mapping[str, object]]:
        """Cross-repo engineering patterns -> ExperienceObject dicts (reusable lessons)."""
        ...

    @abstractmethod
    def normalize(self, snapshot: RepoSnapshot) -> NormalizationResult:
        """Full normalization with provenance; output validates against schemas/."""
        ...
