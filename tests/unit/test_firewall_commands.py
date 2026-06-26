"""Unit tests for local firewall commands."""

import json

from typer.testing import CliRunner

from ui_cli.main import app


runner = CliRunner()


class FakeFirewallClient:
    """Async fake for firewall command tests."""

    instances: list["FakeFirewallClient"] = []
    existing_rules: list[dict] = []

    def __init__(self):
        self.created_payloads: list[dict] = []
        type(self).instances.append(self)

    async def get_firewall_rules(self) -> list[dict]:
        return type(self).existing_rules

    async def create_firewall_rule(self, payload: dict) -> dict:
        self.created_payloads.append(payload)
        return {"_id": "rule-new", **payload}


def reset_fake_client(rules: list[dict] | None = None) -> None:
    FakeFirewallClient.instances = []
    FakeFirewallClient.existing_rules = rules or []


def test_firewall_add_builds_payload_with_before_order(monkeypatch):
    """firewall add builds a classic LAN_IN allow rule payload."""
    reset_fake_client([
        {
            "_id": "allow-existing",
            "name": "Allow existing",
            "ruleset": "LAN_IN",
            "rule_index": 1000,
        },
        {
            "_id": "deny-vlan60",
            "name": "Deny VLAN60 to LAN",
            "ruleset": "LAN_IN",
            "rule_index": 2000,
        },
    ])
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
            "--src",
            "192.168.60.63/32",
            "--dst",
            "192.168.2.120/32",
            "--protocol",
            "tcp",
            "--dst-port",
            "3850",
            "--logging",
            "--before",
            "Deny VLAN60 to LAN",
            "--yes",
            "--output",
            "json",
        ],
        env={"CI": "true"},
    )

    assert result.exit_code == 0, result.output
    payload = FakeFirewallClient.instances[0].created_payloads[0]
    assert payload == {
        "name": "Allow Hermes to MacBook MoneyMoney MCP",
        "enabled": True,
        "ruleset": "LAN_IN",
        "action": "accept",
        "protocol": "tcp",
        "logging": True,
        "src_network_type": "ADDRv4",
        "src_address": "192.168.60.63/32",
        "dst_network_type": "ADDRv4",
        "dst_address": "192.168.2.120/32",
        "dst_port": "3850",
        "rule_index": 1500,
    }
    output = json.loads(result.output)
    assert output["_id"] == "rule-new"
    assert output["rule_index"] == 1500


def test_firewall_add_dry_run_outputs_payload_without_api(monkeypatch):
    """Dry-run mode prints the payload and does not create a rule."""
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
            "--src",
            "192.168.60.63/32",
            "--dst",
            "192.168.2.120/32",
            "--protocol",
            "tcp",
            "--dst-port",
            "3850",
            "--dry-run",
            "--output",
            "json",
        ],
        env={"CI": "true"},
    )

    assert result.exit_code == 0, result.output
    assert FakeFirewallClient.instances == []
    payload = json.loads(result.output)
    assert payload["name"] == "Allow MCP"
    assert payload["ruleset"] == "LAN_IN"
    assert payload["dst_port"] == "3850"


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
            "--dst-port",
            "3850",
            "--yes",
        ],
        env={"CI": "true"},
    )

    assert result.exit_code == 1
    assert "Port filters require" in result.output
