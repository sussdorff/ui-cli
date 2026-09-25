"""Shared pytest fixtures for UI-CLI tests."""

import os
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _isolated_environment(tmp_path_factory, monkeypatch):
    """Keep tests off the developer's home and Git configuration."""
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(home / ".local" / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home / ".cache"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))

# ============================================================
# Mock Data Fixtures
# ============================================================

@pytest.fixture
def mock_hosts_response() -> list[dict[str, Any]]:
    """Sample hosts response from Site Manager API."""
    return [
        {
            "id": "host-001",
            "hardwareId": "hw-001",
            "reportedState": {
                "hostname": "UDM-Pro",
                "ip": "192.168.1.1",
                "mac": "aa:bb:cc:dd:ee:ff",
                "firmwareVersion": "4.0.6",
                "state": "connected",
                "releaseChannel": "release",
            },
            "userData": {"name": "Home Gateway"},
        },
        {
            "id": "host-002",
            "hardwareId": "hw-002",
            "reportedState": {
                "hostname": "Cloud-Key",
                "ip": "192.168.1.2",
                "mac": "11:22:33:44:55:66",
                "firmwareVersion": "3.0.0",
                "state": "connected",
                "releaseChannel": "release",
            },
            "userData": {"name": "Office Controller"},
        },
    ]


@pytest.fixture
def mock_sites_response() -> list[dict[str, Any]]:
    """Sample sites response from Site Manager API."""
    return [
        {
            "siteId": "site-001",
            "siteName": "Home Network",
            "meta": {"timezone": "America/New_York", "desc": "Primary home"},
            "statistics": {"counts": {"totalDevice": 10, "offlineDevice": 1}},
            "isOwner": True,
            "hostId": "host-001",
        },
        {
            "siteId": "site-002",
            "siteName": "Office Network",
            "meta": {"timezone": "America/New_York", "desc": "Work office"},
            "statistics": {"counts": {"totalDevice": 5, "offlineDevice": 0}},
            "isOwner": False,
            "hostId": "host-002",
        },
    ]


@pytest.fixture
def mock_devices_response() -> list[dict[str, Any]]:
    """Sample devices response from Site Manager API."""
    return [
        {
            "id": "dev-001",
            "name": "Living Room AP",
            "model": "U6-Pro",
            "mac": "aa:11:bb:22:cc:33",
            "ip": "192.168.1.100",
            "status": "online",
            "version": "6.6.55",
            "productLine": "network",
            "hostId": "host-001",
        },
        {
            "id": "dev-002",
            "name": "Main Switch",
            "model": "USW-24-POE",
            "mac": "dd:44:ee:55:ff:66",
            "ip": "192.168.1.101",
            "status": "online",
            "version": "7.0.0",
            "productLine": "network",
            "hostId": "host-001",
        },
    ]


@pytest.fixture
def mock_local_clients_response() -> list[dict[str, Any]]:
    """Sample clients response from Local Controller API."""
    return [
        {
            "_id": "client-001",
            "mac": "aa:bb:cc:11:22:33",
            "ip": "10.0.0.100",
            "hostname": "laptop",
            "name": "Work Laptop",
            "is_wired": False,
            "network": "Default",
            "satisfaction": 98,
            "rssi": -45,
            "rx_bytes": 1000000000,
            "tx_bytes": 500000000,
            "uptime": 3600,
        },
        {
            "_id": "client-002",
            "mac": "dd:ee:ff:44:55:66",
            "ip": "10.0.0.101",
            "hostname": "desktop",
            "name": "Gaming PC",
            "is_wired": True,
            "network": "Default",
            "satisfaction": 100,
            "rx_bytes": 5000000000,
            "tx_bytes": 2000000000,
            "uptime": 86400,
        },
    ]


@pytest.fixture
def mock_local_devices_response() -> list[dict[str, Any]]:
    """Sample devices response from Local Controller API."""
    return [
        {
            "_id": "device-001",
            "mac": "70:a7:41:00:00:01",
            "ip": "192.168.1.1",
            "name": "Home Gateway",
            "model": "UDMPROSE",
            "type": "udm",
            "version": "4.0.6",
            "state": 1,
            "uptime": 604800,
            "num_sta": 50,
            "sys_stats": {"loadavg_1": "1.5", "mem_used": 4000000000, "mem_total": 8000000000},
        },
        {
            "_id": "device-002",
            "mac": "70:a7:41:00:00:02",
            "ip": "192.168.1.100",
            "name": "Office AP",
            "model": "U6-Pro",
            "type": "uap",
            "version": "6.6.55",
            "state": 1,
            "uptime": 259200,
            "num_sta": 15,
            "radio_table": [
                {"radio": "ng", "channel": 6},
                {"radio": "na", "channel": 149},
            ],
        },
    ]


@pytest.fixture
def mock_events_response() -> list[dict[str, Any]]:
    """Sample events response from Local Controller API."""
    return [
        {
            "_id": "event-001",
            "time": 1700000000000,
            "key": "EVT_AP_Connected",
            "msg": "AP connected",
            "subsystem": "wlan",
        },
        {
            "_id": "event-002",
            "time": 1700000100000,
            "key": "EVT_SW_Connected",
            "msg": "Switch connected",
            "subsystem": "lan",
        },
    ]


@pytest.fixture
def mock_networks_response() -> list[dict[str, Any]]:
    """Sample networks response from Local Controller API."""
    return [
        {
            "_id": "net-001",
            "name": "Default",
            "vlan": 1,
            "ip_subnet": "192.168.1.0/24",
            "dhcpd_enabled": True,
            "dhcpd_start": "192.168.1.100",
            "dhcpd_stop": "192.168.1.254",
            "purpose": "corporate",
        },
        {
            "_id": "net-002",
            "name": "Guest",
            "vlan": 100,
            "ip_subnet": "192.168.100.0/24",
            "dhcpd_enabled": True,
            "purpose": "guest",
        },
    ]


@pytest.fixture
def mock_vouchers_response() -> list[dict[str, Any]]:
    """Sample vouchers response from Local Controller API."""
    return [
        {
            "_id": "voucher-001",
            "code": "12345-67890",
            "duration": 1440,
            "quota": 1,
            "used": 0,
            "create_time": 1700000000,
            "qos_usage_quota": 1024,
            "note": "Guest access",
        },
        {
            "_id": "voucher-002",
            "code": "abcde-fghij",
            "duration": 60,
            "quota": 5,
            "used": 2,
            "create_time": 1700000000,
            "note": "Event vouchers",
        },
    ]


@pytest.fixture
def mock_daily_stats_response() -> list[dict[str, Any]]:
    """Sample daily stats response from Local Controller API."""
    return [
        {
            "time": 1700000000000,
            "wan-rx_bytes": 50000000000,
            "wan-tx_bytes": 5000000000,
            "num_sta": 80,
        },
        {
            "time": 1699913600000,
            "wan-rx_bytes": 45000000000,
            "wan-tx_bytes": 4500000000,
            "num_sta": 75,
        },
    ]


# ============================================================
# WLAN Fixtures
# ============================================================

@pytest.fixture
def mock_wlans_response() -> list[dict[str, Any]]:
    """Sample WLANs response from Local Controller API."""
    return [
        {
            "_id": "wlan-001",
            "name": "Home WiFi",
            "enabled": True,
            "security": "wpapsk",
            "wpa_mode": "wpa2",
            "vlan": None,
            "hide_ssid": False,
            "pmf_mode": "optional",
            "fast_roaming_enabled": True,
            "wlan_band": "both",
            "is_guest": False,
            "networkconf_id": "net-001",
        },
        {
            "_id": "wlan-002",
            "name": "Guest Network",
            "enabled": True,
            "security": "wpapsk",
            "wpa_mode": "wpa2",
            "vlan": 100,
            "hide_ssid": False,
            "pmf_mode": "disabled",
            "fast_roaming_enabled": False,
            "wlan_band": "both",
            "is_guest": True,
            "guest_lan_isolation": True,
            "networkconf_id": "net-002",
        },
        {
            "_id": "wlan-003",
            "name": "IoT Devices",
            "enabled": True,
            "security": "wpapsk",
            "wpa_mode": "wpa2",
            "vlan": 50,
            "hide_ssid": True,
            "pmf_mode": "disabled",
            "fast_roaming_enabled": False,
            "wlan_band": "2g",
            "is_guest": False,
            "networkconf_id": "net-003",
        },
    ]
