"""Unit tests for local firewall commands (zone-based policies)."""

import json

from typer.testing import CliRunner

from ui_cli.main import app

runner = CliRunner()


# Zone/network fixtures mirroring a real UniFi OS controller layout:
#   192.168.60.0/24 (Services/DMZ) -> zone Dmz
#   192.168.2.0/24  (Management)   -> zone Internal
ZONES = [
    {
        "_id": "zone-internal",
        "name": "Internal",
        "zone_key": "internal",
        "network_ids": ["net-mgmt"],
    },
    {
        "_id": "zone-dmz",
        "name": "Dmz",
        "zone_key": "dmz",
        "network_ids": ["net-dmz"],
    },
]

NETWORKS = [
    {"_id": "net-mgmt", "name": "Management", "ip_subnet": "192.168.2.1/24"},
    {"_id": "net-dmz", "name": "Services/DMZ", "ip_subnet": "192.168.60.1/24"},
]


class FakeFirewallClient:
    """Async fake for firewall command tests."""

    instances: list["FakeFirewallClient"] = []

    def __init__(self):
        self.created_payloads: list[dict] = []
        type(self).instances.append(self)

    async def get_firewall_zones(self) -> list[dict]:
        return ZONES

    async def get_networks(self) -> list[dict]:
        return NETWORKS

    async def create_firewall_policy(self, payload: dict) -> dict:
        self.created_payloads.append(payload)
        return {"_id": "policy-new", **payload}


def reset_fake_client() -> None:
    FakeFirewallClient.instances = []


def created_payloads() -> list[dict]:
    return [p for inst in FakeFirewallClient.instances for p in inst.created_payloads]


def test_firewall_add_builds_zone_policy_payload(monkeypatch):
    """firewall add resolves zones from IPs and builds an ALLOW policy."""
    reset_fake_client()
    monkeypatch.setattr(
        "ui_cli.commands.local.firewall.UniFiLocalClient",
        FakeFirewallClient,
    )

    result = runner.invoke(
        app,
        [
            "lo",
            "firewall",
            "add",
            "Allow Hermes to MacBook MoneyMoney MCP",
            "--ruleset",
            "LAN_IN",
            "--action",
            "accept",
            "--protocol",
            "tcp",
            "--src",
            "192.168.60.63/32",
            "--dst",
            "192.168.2.120/32",
            "--dst-port",
            "3850",
            "--logging",
            "--yes",
            "--output",
            "json",
        ],
        env={"CI": "true"},
    )

    assert result.exit_code == 0, result.output
    payloads = created_payloads()
    assert len(payloads) == 1
    payload = payloads[0]

    assert payload["name"] == "Allow Hermes to MacBook MoneyMoney MCP"
    assert payload["action"] == "ALLOW"
    assert payload["protocol"] == "tcp"
    assert payload["logging"] is True
    assert payload["enabled"] is True
    assert payload["ip_version"] == "IPV4"
    assert payload["create_allow_respond"] is True

    # Source resolved to Dmz, host IP, no port match.
    assert payload["source"]["zone_id"] == "zone-dmz"
    assert payload["source"]["matching_target"] == "IP"
    assert payload["source"]["ips"] == ["192.168.60.63"]
    assert payload["source"]["port_matching_type"] == "ANY"

    # Destination resolved to Internal, host IP, specific port 3850.
    assert payload["destination"]["zone_id"] == "zone-internal"
    assert payload["destination"]["matching_target"] == "IP"
    assert payload["destination"]["ips"] == ["192.168.2.120"]
    assert payload["destination"]["port_matching_type"] == "SPECIFIC"
    assert payload["destination"]["port"] == "3850"

    output = json.loads(result.output)
    assert output["_id"] == "policy-new"


def test_firewall_add_dry_run_does_not_create(monkeypatch):
    """Dry-run prints the payload and does not create a policy."""
    reset_fake_client()
    monkeypatch.setattr(
        "ui_cli.commands.local.firewall.UniFiLocalClient",
        FakeFirewallClient,
    )

    result = runner.invoke(
        app,
        [
            "lo",
            "firewall",
            "add",
            "Allow MCP",
            "--protocol",
            "tcp",
            "--src",
            "192.168.60.63",
            "--dst",
            "192.168.2.120",
            "--dst-port",
            "3850",
            "--dry-run",
            "--output",
            "json",
        ],
        env={"CI": "true"},
    )

    assert result.exit_code == 0, result.output
    assert created_payloads() == []
    payload = json.loads(result.output)
    assert payload["name"] == "Allow MCP"
    assert payload["action"] == "ALLOW"
    assert payload["destination"]["port"] == "3850"
    assert payload["source"]["zone_id"] == "zone-dmz"
    assert payload["destination"]["zone_id"] == "zone-internal"


def test_firewall_add_explicit_zones(monkeypatch):
    """Explicit --src-zone/--dst-zone override auto-resolution."""
    reset_fake_client()
    monkeypatch.setattr(
        "ui_cli.commands.local.firewall.UniFiLocalClient",
        FakeFirewallClient,
    )

    result = runner.invoke(
        app,
        [
            "lo",
            "firewall",
            "add",
            "Block external",
            "--action",
            "drop",
            "--src-zone",
            "external",
            "--dst-zone",
            "Internal",
            "--dst",
            "192.168.2.120",
            "--yes",
            "--output",
            "json",
        ],
        env={"CI": "true"},
    )

    # 'external' is not in the fixture zones -> resolution error.
    assert result.exit_code == 1
    assert "Unknown firewall zone" in result.output


def test_firewall_add_rejects_port_with_all_protocol(monkeypatch):
    """Ports require a TCP/UDP protocol."""
    reset_fake_client()
    monkeypatch.setattr(
        "ui_cli.commands.local.firewall.UniFiLocalClient",
        FakeFirewallClient,
    )

    result = runner.invoke(
        app,
        [
            "lo",
            "firewall",
            "add",
            "Invalid",
            "--src",
            "192.168.60.63",
            "--dst",
            "192.168.2.120",
            "--dst-port",
            "3850",
            "--yes",
        ],
        env={"CI": "true"},
    )

    assert result.exit_code == 1
    assert "Port filters require" in result.output


def test_firewall_add_rejects_subnet(monkeypatch):
    """Subnet sources are rejected with a helpful message."""
    reset_fake_client()
    monkeypatch.setattr(
        "ui_cli.commands.local.firewall.UniFiLocalClient",
        FakeFirewallClient,
    )

    result = runner.invoke(
        app,
        [
            "lo",
            "firewall",
            "add",
            "Subnet rule",
            "--src",
            "192.168.60.0/24",
            "--dst",
            "192.168.2.120",
            "--yes",
        ],
        env={"CI": "true"},
    )

    assert result.exit_code == 1
    assert "subnet" in result.output.lower()


def test_firewall_add_unresolvable_ip(monkeypatch):
    """An IP that maps to no network errors and asks for an explicit zone."""
    reset_fake_client()
    monkeypatch.setattr(
        "ui_cli.commands.local.firewall.UniFiLocalClient",
        FakeFirewallClient,
    )

    result = runner.invoke(
        app,
        [
            "lo",
            "firewall",
            "add",
            "Stray IP",
            "--src",
            "10.99.99.99",
            "--dst",
            "192.168.2.120",
            "--yes",
        ],
        env={"CI": "true"},
    )

    assert result.exit_code == 1
    assert "Could not map src IP" in result.output
