# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-04-29

### Changed
- `QuerySet.update()` now saves history automatically — **breaking change**. Previously `filter(...).update(...)` bypassed `post_save` signals and produced no history records; now it captures the pre-update state and creates history entries like any other tracked mutation.

### Added
- `QuerySet.update_without_history(**kwargs)` — explicit opt-out for cases where `update()` should not produce history records (seed data, internal bookkeeping, etc.).

## [2.0.1] - 2026-04-26

### Changed
- Rewrote README: added problem statement, architecture overview, DRF usage examples, data model diagram, and key features table.

## [2.0.0] - 2026-04-24

### Changed
- Renamed `project` field to `scope` across the entire codebase — **breaking change**, requires a database migration.
- Changed `object_id` field type from `IntegerField` to `TextField` to support non-integer primary keys — **breaking change**, requires a database migration.

## [1.0.2] - 2026-04-24

### Removed
- Removed `deepdiff` dependency — package no longer requires it.

## [1.0.1] - 2026-04-24

### Changed
- Added full package metadata to `pyproject.toml`: description, authors, maintainers, keywords, classifiers, and project URLs.
