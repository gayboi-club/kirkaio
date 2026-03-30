# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-30

### Added
- Initial production release.
- Complete async `KirkaClient` with support for all public API endpoints.
- Automatic TTL caching with configurable expiration.
- Robust 429 Rate Limit handling with auto-retry.
- Full CLI tool with subcommands for users, clans, leaderboards, and quests.
- Comprehensive test suite with 94% code coverage.
- Extensive documentation and usage examples.

### Changed
- Reorganized project into a proper Python package structure.
- Migrated CLI from Typer to Argparse for better dependency management.

### Fixed
- Fixed bug where empty cache objects evaluated to False.
- Fixed various model serialization edge cases.
