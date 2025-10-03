#!/usr/bin/env python3
"""
StillMe AgentDev - Threat Intelligence
Enterprise-grade threat intelligence and security analytics
"""

import asyncio
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
import requests
import yaml


class ThreatType(Enum):
    """Threat intelligence categories"""

    MALWARE = "malware"
    PHISHING = "phishing"
    BOTNET = "botnet"
    EXPLOIT = "exploit"
    VULNERABILITY = "vulnerability"
    IP_REPUTATION = "ip_reputation"
    DOMAIN_REPUTATION = "domain_reputation"
    FILE_HASH = "file_hash"
    URL_REPUTATION = "url_reputation"


class ThreatSeverity(Enum):
    """Threat severity levels"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ThreatIndicator:
    """Threat intelligence indicator"""

    indicator_id: str
    indicator_type: ThreatType
    value: str
    severity: ThreatSeverity
    confidence: float
    source: str
    first_seen: float
    last_seen: float
    tags: list[str]
    metadata: dict[str, Any]


@dataclass
class ThreatReport:
    """Threat intelligence report"""

    report_id: str
    title: str
    description: str
    threat_type: ThreatType
    severity: ThreatSeverity
    indicators: list[ThreatIndicator]
    created_at: float
    updated_at: float
    source: str
    references: list[str]


class ThreatIntelligence:
    """Enterprise threat intelligence system"""

    def __init__(self, config_path: str | None = None):
        self.config = self._load_config(config_path)
        self.indicators: dict[str, ThreatIndicator] = {}
        self.reports: dict[str, ThreatReport] = {}
        self.blocked_indicators: set[str] = set()
        self.intelligence_sources = self._load_intelligence_sources()
        self.update_interval = self.config.get("update_interval", 3600)  # 1 hour
        self.running = False

    def _load_config(self, config_path: str | None = None) -> dict[str, Any]:
        """Load threat intelligence configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/threat_intelligence.yaml")

        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        else:
            return {
                "update_interval": 3600,
                "sources": {
                    "enabled": ["virustotal", "abuseipdb", "malware_domains"],
                    "api_keys": {"virustotal": None, "abuseipdb": None},
                },
                "blocking": {
                    "auto_block": True,
                    "block_threshold": 0.8,
                    "whitelist": [],
                },
                "cache": {
                    "enabled": True,
                    "ttl": 86400,  # 24 hours
                    "max_size": 10000,
                },
            }

    def _load_intelligence_sources(self) -> dict[str, dict[str, Any]]:
        """Load threat intelligence sources configuration"""
        return {
            "virustotal": {
                "name": "VirusTotal",
                "api_url": "https://www.virustotal.com/vtapi/v2",
                "enabled": True,
                "rate_limit": 4,  # requests per minute
                "last_request": 0,
            },
            "abuseipdb": {
                "name": "AbuseIPDB",
                "api_url": "https://api.abuseipdb.com/api/v2",
                "enabled": True,
                "rate_limit": 1000,  # requests per day
                "last_request": 0,
            },
            "malware_domains": {
                "name": "Malware Domains",
                "url": "https://mirror1.malwaredomains.com/files/domains.txt",
                "enabled": True,
                "last_update": 0,
            },
            "openphish": {
                "name": "OpenPhish",
                "url": "https://openphish.com/feed.txt",
                "enabled": True,
                "last_update": 0,
            },
        }

    def _calculate_indicator_hash(self, indicator_type: ThreatType, value: str) -> str:
        """Calculate hash for threat indicator"""
        return hashlib.sha256(f"{indicator_type.value}:{value}".encode()).hexdigest()

    def add_indicator(
        self,
        indicator_type: ThreatType,
        value: str,
        severity: ThreatSeverity,
        confidence: float,
        source: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add threat indicator"""
        indicator_id = self._calculate_indicator_hash(indicator_type, value)

        if indicator_id in self.indicators:
            # Update existing indicator
            existing = self.indicators[indicator_id]
            existing.last_seen = time.time()
            existing.confidence = max(existing.confidence, confidence)
            existing.tags = list(set(existing.tags + (tags or [])))
            existing.metadata.update(metadata or {})
        else:
            # Create new indicator
            indicator = ThreatIndicator(
                indicator_id=indicator_id,
                indicator_type=indicator_type,
                value=value,
                severity=severity,
                confidence=confidence,
                source=source,
                first_seen=time.time(),
                last_seen=time.time(),
                tags=tags or [],
                metadata=metadata or {},
            )
            self.indicators[indicator_id] = indicator

        # Auto-block if configured
        if (
            self.config["blocking"]["auto_block"]
            and confidence >= self.config["blocking"]["block_threshold"]
            and value not in self.config["blocking"]["whitelist"]
        ):
            self.blocked_indicators.add(indicator_id)
            print(f"🚫 Auto-blocked threat indicator: {value}")

        return indicator_id

    def check_indicator(
        self, indicator_type: ThreatType, value: str
    ) -> ThreatIndicator | None:
        """Check if indicator is known threat"""
        indicator_id = self._calculate_indicator_hash(indicator_type, value)
        return self.indicators.get(indicator_id)

    def is_blocked(self, indicator_type: ThreatType, value: str) -> bool:
        """Check if indicator is blocked"""
        indicator_id = self._calculate_indicator_hash(indicator_type, value)
        return indicator_id in self.blocked_indicators

    def unblock_indicator(self, indicator_type: ThreatType, value: str) -> bool:
        """Unblock threat indicator"""
        indicator_id = self._calculate_indicator_hash(indicator_type, value)
        if indicator_id in self.blocked_indicators:
            self.blocked_indicators.remove(indicator_id)
            print(f"✅ Unblocked threat indicator: {value}")
            return True
        return False

    async def _fetch_virustotal_data(
        self, indicator_type: ThreatType, value: str
    ) -> dict[str, Any] | None:
        """Fetch data from VirusTotal API"""
        api_key = self.config["sources"]["api_keys"].get("virustotal")
        if not api_key:
            return None

        source_config = self.intelligence_sources["virustotal"]

        # Rate limiting
        current_time = time.time()
        if (
            current_time - source_config["last_request"]
            < 60 / source_config["rate_limit"]
        ):
            await asyncio.sleep(60 / source_config["rate_limit"])

        try:
            if indicator_type == ThreatType.IP_REPUTATION:
                url = f"{source_config['api_url']}/ip-address/report"
                params = {"apikey": api_key, "ip": value}
            elif indicator_type == ThreatType.DOMAIN_REPUTATION:
                url = f"{source_config['api_url']}/domain/report"
                params = {"apikey": api_key, "domain": value}
            elif indicator_type == ThreatType.FILE_HASH:
                url = f"{source_config['api_url']}/file/report"
                params = {"apikey": api_key, "resource": value}
            elif indicator_type == ThreatType.URL_REPUTATION:
                url = f"{source_config['api_url']}/url/report"
                params = {"apikey": api_key, "resource": value}
            else:
                return None

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            source_config["last_request"] = time.time()
            return response.json()

        except Exception as e:
            print(f"⚠️ VirusTotal API error: {e}")
            return None

    async def _fetch_abuseipdb_data(self, ip: str) -> dict[str, Any] | None:
        """Fetch data from AbuseIPDB API"""
        api_key = self.config["sources"]["api_keys"].get("abuseipdb")
        if not api_key:
            return None

        source_config = self.intelligence_sources["abuseipdb"]

        try:
            url = f"{source_config['api_url']}/check"
            headers = {"Key": api_key, "Accept": "application/json"}
            params = {"ipAddress": ip, "maxAgeInDays": 90, "verbose": ""}

            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            source_config["last_request"] = time.time()
            return response.json()

        except Exception as e:
            print(f"⚠️ AbuseIPDB API error: {e}")
            return None

    async def _fetch_malware_domains(self) -> list[str]:
        """Fetch malware domains list"""
        source_config = self.intelligence_sources["malware_domains"]

        try:
            response = requests.get(source_config["url"], timeout=30)
            response.raise_for_status()

            domains = []
            for line in response.text.split("\n"):
                if line.strip() and not line.startswith("#"):
                    parts = line.split("\t")
                    if len(parts) > 1:
                        domains.append(parts[1].strip())

            source_config["last_update"] = time.time()
            return domains

        except Exception as e:
            print(f"⚠️ Malware domains fetch error: {e}")
            return []

    async def _fetch_openphish_urls(self) -> list[str]:
        """Fetch OpenPhish phishing URLs"""
        source_config = self.intelligence_sources["openphish"]

        try:
            response = requests.get(source_config["url"], timeout=30)
            response.raise_for_status()

            urls = [line.strip() for line in response.text.split("\n") if line.strip()]
            source_config["last_update"] = time.time()
            return urls

        except Exception as e:
            print(f"⚠️ OpenPhish fetch error: {e}")
            return []

    async def update_intelligence(self):
        """Update threat intelligence from all sources"""
        print("🔄 Updating threat intelligence...")

        # Update malware domains
        if "malware_domains" in self.config["sources"]["enabled"]:
            domains = await self._fetch_malware_domains()
            for domain in domains:
                self.add_indicator(
                    indicator_type=ThreatType.DOMAIN_REPUTATION,
                    value=domain,
                    severity=ThreatSeverity.HIGH,
                    confidence=0.9,
                    source="malware_domains",
                    tags=["malware", "domain"],
                )

        # Update phishing URLs
        if "openphish" in self.config["sources"]["enabled"]:
            urls = await self._fetch_openphish_urls()
            for url in urls:
                self.add_indicator(
                    indicator_type=ThreatType.URL_REPUTATION,
                    value=url,
                    severity=ThreatSeverity.HIGH,
                    confidence=0.8,
                    source="openphish",
                    tags=["phishing", "url"],
                )

        print(f"✅ Threat intelligence updated: {len(self.indicators)} indicators")

    async def analyze_artifact(
        self, artifact_type: str, artifact_value: str
    ) -> dict[str, Any]:
        """Analyze artifact against threat intelligence"""
        analysis_result = {
            "artifact_type": artifact_type,
            "artifact_value": artifact_value,
            "threat_detected": False,
            "threat_level": None,
            "confidence": 0.0,
            "sources": [],
            "recommendations": [],
        }

        # Map artifact type to threat type
        type_mapping = {
            "ip": ThreatType.IP_REPUTATION,
            "domain": ThreatType.DOMAIN_REPUTATION,
            "url": ThreatType.URL_REPUTATION,
            "file_hash": ThreatType.FILE_HASH,
            "email": ThreatType.PHISHING,
        }

        threat_type = type_mapping.get(artifact_type)
        if not threat_type:
            return analysis_result

        # Check local indicators
        indicator = self.check_indicator(threat_type, artifact_value)
        if indicator:
            analysis_result.update(
                {
                    "threat_detected": True,
                    "threat_level": indicator.severity.value,
                    "confidence": indicator.confidence,
                    "sources": [indicator.source],
                    "recommendations": ["Block access", "Investigate further"],
                }
            )
            return analysis_result

        # Check external sources
        if threat_type == ThreatType.IP_REPUTATION:
            vt_data = await self._fetch_virustotal_data(threat_type, artifact_value)
            abuse_data = await self._fetch_abuseipdb_data(artifact_value)

            if vt_data and vt_data.get("response_code") == 1:
                positives = vt_data.get("positives", 0)
                total = vt_data.get("total", 1)
                confidence = positives / total

                if confidence > 0.1:  # 10% detection threshold
                    analysis_result.update(
                        {
                            "threat_detected": True,
                            "threat_level": "HIGH" if confidence > 0.5 else "MEDIUM",
                            "confidence": confidence,
                            "sources": ["virustotal"],
                            "recommendations": [
                                "Block IP address",
                                "Monitor for additional activity",
                            ],
                        }
                    )

            if (
                abuse_data
                and abuse_data.get("data", {}).get("abuseConfidencePercentage", 0) > 25
            ):
                confidence = abuse_data["data"]["abuseConfidencePercentage"] / 100
                analysis_result.update(
                    {
                        "threat_detected": True,
                        "threat_level": "HIGH" if confidence > 0.75 else "MEDIUM",
                        "confidence": confidence,
                        "sources": ["abuseipdb"],
                        "recommendations": ["Block IP address", "Report to abuse team"],
                    }
                )

        return analysis_result

    def get_threat_statistics(self) -> dict[str, Any]:
        """Get threat intelligence statistics"""
        total_indicators = len(self.indicators)
        blocked_indicators = len(self.blocked_indicators)

        indicators_by_type = {}
        indicators_by_severity = {}

        for indicator in self.indicators.values():
            # Count by type
            indicator_type = indicator.indicator_type.value
            indicators_by_type[indicator_type] = (
                indicators_by_type.get(indicator_type, 0) + 1
            )

            # Count by severity
            severity = indicator.severity.value
            indicators_by_severity[severity] = (
                indicators_by_severity.get(severity, 0) + 1
            )

        return {
            "total_indicators": total_indicators,
            "blocked_indicators": blocked_indicators,
            "indicators_by_type": indicators_by_type,
            "indicators_by_severity": indicators_by_severity,
            "sources_active": len(
                [
                    s
                    for s in self.intelligence_sources.values()
                    if s.get("enabled", False)
                ]
            ),
            "last_update": max(
                [s.get("last_update", 0) for s in self.intelligence_sources.values()]
            ),
        }

    async def start_intelligence_service(self):
        """Start threat intelligence service"""
        if self.running:
            return

        self.running = True
        print("🕵️ Threat Intelligence service started")

        # Initial update
        await self.update_intelligence()

        # Periodic updates
        while self.running:
            await asyncio.sleep(self.update_interval)
            await self.update_intelligence()

    def stop_intelligence_service(self):
        """Stop threat intelligence service"""
        self.running = False
        print("🛑 Threat Intelligence service stopped")

    async def export_intelligence(self, file_path: str):
        """Export threat intelligence to file"""
        try:
            export_data = {
                "indicators": [
                    asdict(indicator) for indicator in self.indicators.values()
                ],
                "reports": [asdict(report) for report in self.reports.values()],
                "blocked_indicators": list(self.blocked_indicators),
                "statistics": self.get_threat_statistics(),
                "export_timestamp": time.time(),
            }

            async with aiofiles.open(file_path, "w") as f:
                await f.write(json.dumps(export_data, indent=2))

            print(f"📄 Threat intelligence exported to: {file_path}")

        except Exception as e:
            print(f"⚠️ Failed to export threat intelligence: {e}")


# Global threat intelligence instance
threat_intelligence = ThreatIntelligence()


# Convenience functions
async def start_threat_intelligence():
    """Start threat intelligence service"""
    await threat_intelligence.start_intelligence_service()


def stop_threat_intelligence():
    """Stop threat intelligence service"""
    threat_intelligence.stop_intelligence_service()


def check_threat(artifact_type: str, artifact_value: str) -> ThreatIndicator | None:
    """Check if artifact is a known threat"""
    type_mapping = {
        "ip": ThreatType.IP_REPUTATION,
        "domain": ThreatType.DOMAIN_REPUTATION,
        "url": ThreatType.URL_REPUTATION,
        "file_hash": ThreatType.FILE_HASH,
    }

    threat_type = type_mapping.get(artifact_type)
    if threat_type:
        return threat_intelligence.check_indicator(threat_type, artifact_value)
    return None


async def analyze_artifact(artifact_type: str, artifact_value: str) -> dict[str, Any]:
    """Analyze artifact against threat intelligence"""
    return await threat_intelligence.analyze_artifact(artifact_type, artifact_value)


if __name__ == "__main__":

    async def main():
        # Example usage
        ti = ThreatIntelligence()

        # Start intelligence service
        await ti.start_intelligence_service()

        # Analyze some artifacts
        result1 = await ti.analyze_artifact("ip", "8.8.8.8")
        print(f"IP Analysis: {result1}")

        result2 = await ti.analyze_artifact("domain", "google.com")
        print(f"Domain Analysis: {result2}")

        # Get statistics
        stats = ti.get_threat_statistics()
        print(f"Threat Statistics: {stats}")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            ti.stop_intelligence_service()

    asyncio.run(main())
