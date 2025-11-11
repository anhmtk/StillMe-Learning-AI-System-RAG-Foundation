# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Model cache system (`ModelManager`) to prevent re-downloading all-MiniLM-L6-v2 on every deploy
- Debug endpoints (`/api/debug/cache-status`, `/api/debug/model-status`, `/api/debug/environment`) for monitoring
- Automatic foundational knowledge check and add on Railway deployment
- Improved StillMe query detection for technical questions (embedding, model, database)
- Model warmup script for Docker build phase

### Changed
- Dockerfile: Use separate `model_warmup.py` script instead of inline Python command
- EmbeddingService: Now uses ModelManager for cache verification and environment setup
- README: Updated docker-compose → docker compose (v2 syntax)
- README: Added security warnings for `.env` file
- README: Added Table of Contents for better navigation
- README: Updated validator chain claim wording (see [Claims & Evaluation](docs/CLAIMS_AND_EVAL.md))

### Fixed
- Fixed SyntaxError in Dockerfile model pre-download command
- Fixed issue where foundational knowledge wasn't retrieved for technical questions
- Fixed model re-downloading issue on Railway deployments

## [0.6.2] - 2025-01-XX

### Added
- Continuum Memory System (L0-L3 tiers)
- Multi-Source Learning (RSS, arXiv, CrossRef, Wikipedia)
- Nested Learning experimental branch

### Changed
- Improved RAG retrieval with foundational knowledge prioritization
- Enhanced validation chain with confidence scoring

## [0.6.1] - 2024-XX-XX

### Added
- Validator Chain implementation
- Confidence scoring system
- Dashboard with validation metrics

### Changed
- Improved error handling
- Enhanced logging

## [0.6.0] - 2024-XX-XX

### Added
- Initial RAG system
- ChromaDB integration
- FastAPI backend
- Streamlit dashboard

---

## Version History

- **v0.6.x**: MVP with RAG + Validators + Dashboard
- **v0.5.x**: Core RAG implementation
- **v0.4.x**: Docker setup and deployment
- **v0.3.x**: Initial architecture
- **v0.2.x**: Proof of concept
- **v0.1.x**: Initial project setup

---

## Notes

- For detailed architecture changes, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- For breaking changes, see migration guides in [docs/](docs/)
- For security updates, see [docs/SECURITY.md](docs/SECURITY.md)

