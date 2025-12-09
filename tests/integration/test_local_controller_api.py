"""Integration tests for Local Controller API (require real controller access)."""

import pytest

from ui_cli.local_client import UniFiLocalClient


@pytest.mark.integration
class TestLocalControllerAPIIntegration:
    """Integration tests for Local Controller API."""

    @pytest.fixture
    def client(self, integration_env_vars):
        """Create a real Local Controller client."""
        return UniFiLocalClient()

    @pytest.mark.asyncio
    async def test_list_clients(self, client):
        """Test listing clients from real controller."""
        clients = await client.list_clients()

        assert isinstance(clients, list)
        if clients:
            c = clients[0]
            assert "mac" in c

    @pytest.mark.asyncio
    async def test_get_devices(self, client):
        """Test getting devices from real controller."""
        devices = await client.get_devices()

        assert isinstance(devices, list)
        assert len(devices) > 0  # Should have at least the controller itself

        device = devices[0]
        assert "mac" in device
        assert "model" in device

    @pytest.mark.asyncio
    async def test_get_events(self, client):
        """Test getting events from real controller."""
        events = await client.get_events(limit=10)

        assert isinstance(events, list)
        if events:
            event = events[0]
            assert "time" in event or "datetime" in event

    @pytest.mark.asyncio
    async def test_get_health(self, client):
        """Test getting health from real controller."""
        health = await client.get_health()

        assert isinstance(health, list)
        assert len(health) > 0

        # Should have subsystem info
        subsystems = [h.get("subsystem") for h in health]
        assert any(s in subsystems for s in ["wlan", "wan", "lan", "www"])

    @pytest.mark.asyncio
    async def test_get_networks(self, client):
        """Test getting networks from real controller."""
        networks = await client.get_networks()

        assert isinstance(networks, list)
        assert len(networks) > 0  # Should have at least default network

        network = networks[0]
        assert "name" in network

    @pytest.mark.asyncio
    async def test_get_vouchers(self, client):
        """Test getting vouchers from real controller."""
        vouchers = await client.get_vouchers()

        assert isinstance(vouchers, list)
        # May be empty if no vouchers exist

    @pytest.mark.asyncio
    async def test_get_daily_stats(self, client):
        """Test getting daily stats from real controller."""
        stats = await client.get_daily_stats(days=7)

        assert isinstance(stats, list)
        if stats:
            stat = stats[0]
            assert "time" in stat

    @pytest.mark.asyncio
    async def test_get_hourly_stats(self, client):
        """Test getting hourly stats from real controller."""
        stats = await client.get_hourly_stats(hours=24)

        assert isinstance(stats, list)
        if stats:
            stat = stats[0]
            assert "time" in stat

    @pytest.mark.asyncio
    async def test_get_firewall_rules(self, client):
        """Test getting firewall rules from real controller."""
        rules = await client.get_firewall_rules()

        assert isinstance(rules, list)
        # May be empty if no custom rules

    @pytest.mark.asyncio
    async def test_get_port_forwards(self, client):
        """Test getting port forwards from real controller."""
        forwards = await client.get_port_forwards()

        assert isinstance(forwards, list)
        # May be empty if no port forwards configured


@pytest.mark.integration
class TestLocalControllerReadOnlyActions:
    """Integration tests for read-only controller actions."""

    @pytest.fixture
    def client(self, integration_env_vars):
        """Create a real Local Controller client."""
        return UniFiLocalClient()

    @pytest.mark.asyncio
    async def test_get_site_dpi(self, client):
        """Test getting site DPI stats."""
        dpi = await client.get_site_dpi()

        assert isinstance(dpi, list)
        # May be empty if DPI not enabled

    @pytest.mark.asyncio
    async def test_get_alarms(self, client):
        """Test getting alarms."""
        alarms = await client.get_alarms()

        assert isinstance(alarms, list)
        # May be empty if no alarms


@pytest.mark.integration
class TestLocalControllerWlanAPI:
    """Integration tests for WLAN management."""

    @pytest.fixture
    def client(self, integration_env_vars):
        """Create a real Local Controller client."""
        return UniFiLocalClient()

    @pytest.mark.asyncio
    async def test_get_wlans(self, client):
        """Test getting WLANs from real controller."""
        wlans = await client.get_wlans()

        assert isinstance(wlans, list)
        assert len(wlans) > 0  # Should have at least one WLAN

        wlan = wlans[0]
        assert "_id" in wlan
        assert "name" in wlan
        assert "security" in wlan


@pytest.mark.integration
class TestLocalControllerAPGroupAPI:
    """Integration tests for AP group (broadcasting group) management."""

    @pytest.fixture
    def client(self, integration_env_vars):
        """Create a real Local Controller client."""
        return UniFiLocalClient()

    @pytest.mark.asyncio
    async def test_get_ap_groups(self, client):
        """Test getting AP groups from real controller."""
        groups = await client.get_ap_groups()

        assert isinstance(groups, list)
        assert len(groups) > 0  # Should have at least 'All APs'

        group = groups[0]
        assert "_id" in group
        assert "name" in group
        assert "device_macs" in group

    @pytest.mark.asyncio
    async def test_ap_group_crud_cycle(self, client):
        """Test full CRUD cycle for AP groups."""
        # Create a test group
        test_group_name = "UI-CLI Test AP Group"
        created = await client.create_ap_group(test_group_name)

        assert created["name"] == test_group_name
        assert created.get("device_macs", []) == []
        group_id = created["_id"]

        try:
            # Verify group appears in list
            groups = await client.get_ap_groups()
            group_ids = [g["_id"] for g in groups]
            assert group_id in group_ids

            # Update group (add a device MAC - using a fake one for test)
            # Note: Using a real device MAC would require knowing one exists
            updated = await client.update_ap_group(
                group_id, test_group_name, []
            )
            assert updated["name"] == test_group_name

        finally:
            # Clean up: delete the test group
            success = await client.delete_ap_group(group_id)
            assert success is True

            # Verify group is deleted
            groups = await client.get_ap_groups()
            group_ids = [g["_id"] for g in groups]
            assert group_id not in group_ids
