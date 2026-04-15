"""Unit tests for Local Controller API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ui_cli.local_client import (
    LocalAPIError,
    LocalAuthenticationError,
    UniFiLocalClient,
)


class TestUniFiLocalClientInit:
    """Tests for Local Controller client initialization."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("ui_cli.local_client.settings") as mock:
            mock.controller_url = "https://192.168.1.1"
            mock.controller_username = "admin"
            mock.controller_password = "password"
            mock.controller_api_key = ""
            mock.controller_site = "default"
            mock.controller_verify_ssl = False
            mock.timeout = 30
            mock.session_file = MagicMock()
            mock.session_file.exists.return_value = False
            yield mock

    def test_client_initialization(self, mock_settings):
        """Test client initializes with correct settings."""
        client = UniFiLocalClient()
        assert client.controller_url == "https://192.168.1.1"
        assert client.username == "admin"
        assert client.site == "default"

    def test_client_without_url_raises_error(self, mock_settings):
        """Test client raises error when URL is missing."""
        mock_settings.controller_url = ""
        with pytest.raises(LocalAuthenticationError, match="URL not configured"):
            UniFiLocalClient()

    def test_client_without_credentials_raises_error(self, mock_settings):
        """Test client raises error when credentials are missing."""
        mock_settings.controller_username = None
        with pytest.raises(LocalAuthenticationError, match="credentials not configured"):
            UniFiLocalClient()

    def test_api_prefix_for_udm(self, mock_settings):
        """Test API prefix for UDM controllers."""
        client = UniFiLocalClient()
        client._is_udm = True
        assert "/proxy/network/api/s/default" in client.api_prefix

    def test_api_prefix_for_cloud_key(self, mock_settings):
        """Test API prefix for Cloud Key controllers."""
        client = UniFiLocalClient()
        client._is_udm = False
        assert "/api/s/default" in client.api_prefix
        assert "/proxy/network" not in client.api_prefix


class TestUniFiLocalClientMethods:
    """Tests for Local Controller client methods."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("ui_cli.local_client.settings") as mock:
            mock.controller_url = "https://192.168.1.1"
            mock.controller_username = "admin"
            mock.controller_password = "password"
            mock.controller_api_key = ""
            mock.controller_site = "default"
            mock.controller_verify_ssl = False
            mock.timeout = 30
            mock.session_file = MagicMock()
            mock.session_file.exists.return_value = False
            yield mock

    @pytest.mark.asyncio
    async def test_list_clients(self, mock_settings, mock_local_clients_response):
        """Test listing clients."""
        client = UniFiLocalClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": mock_local_clients_response}

            clients = await client.list_clients()

            assert len(clients) == 2
            assert clients[0]["mac"] == "aa:bb:cc:11:22:33"

    @pytest.mark.asyncio
    async def test_get_devices(self, mock_settings, mock_local_devices_response):
        """Test getting devices."""
        client = UniFiLocalClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": mock_local_devices_response}

            devices = await client.get_devices()

            assert len(devices) == 2
            assert devices[0]["name"] == "Home Gateway"

    @pytest.mark.asyncio
    async def test_get_events(self, mock_settings, mock_events_response):
        """Test getting events."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"data": mock_events_response}

            events = await client.get_events(limit=50)

            assert len(events) == 2
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_networks(self, mock_settings, mock_networks_response):
        """Test getting networks."""
        client = UniFiLocalClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": mock_networks_response}

            networks = await client.get_networks()

            assert len(networks) == 2
            assert networks[0]["name"] == "Default"

    @pytest.mark.asyncio
    async def test_get_vouchers(self, mock_settings, mock_vouchers_response):
        """Test getting vouchers."""
        client = UniFiLocalClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": mock_vouchers_response}

            vouchers = await client.get_vouchers()

            assert len(vouchers) == 2
            assert vouchers[0]["code"] == "12345-67890"

    @pytest.mark.asyncio
    async def test_get_daily_stats(self, mock_settings, mock_daily_stats_response):
        """Test getting daily stats."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"data": mock_daily_stats_response}

            stats = await client.get_daily_stats(days=7)

            assert len(stats) == 2
            assert stats[0]["num_sta"] == 80

    @pytest.mark.asyncio
    async def test_restart_device(self, mock_settings):
        """Test restarting a device."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"meta": {"rc": "ok"}}

            success = await client.restart_device("aa:bb:cc:dd:ee:ff")

            assert success is True
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "restart" in str(call_args)

    @pytest.mark.asyncio
    async def test_block_client(self, mock_settings):
        """Test blocking a client."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"meta": {"rc": "ok"}}

            success = await client.block_client("aa:bb:cc:dd:ee:ff")

            assert success is True

    @pytest.mark.asyncio
    async def test_create_voucher(self, mock_settings):
        """Test creating a voucher."""
        client = UniFiLocalClient()

        with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"data": [{"create_time": 1700000000}]}

            result = await client.create_voucher(
                count=1,
                duration=1440,
                quota=0,
                up_limit=0,
                down_limit=0,
                multi_use=1,
                note="Test",
            )

            assert len(result) == 1


class TestUniFiLocalClientWlanMethods:
    """Tests for WLAN methods."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("ui_cli.local_client.settings") as mock:
            mock.controller_url = "https://192.168.1.1"
            mock.controller_username = "admin"
            mock.controller_password = "password"
            mock.controller_api_key = ""
            mock.controller_site = "default"
            mock.controller_verify_ssl = False
            mock.timeout = 30
            mock.session_file = MagicMock()
            mock.session_file.exists.return_value = False
            yield mock

    @pytest.mark.asyncio
    async def test_get_wlans(self, mock_settings, mock_wlans_response):
        """Test getting WLANs."""
        client = UniFiLocalClient()

        with patch.object(client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"data": mock_wlans_response}

            wlans = await client.get_wlans()

            assert len(wlans) == 3
            assert wlans[0]["name"] == "Home WiFi"
            assert wlans[1]["is_guest"] is True
            mock_get.assert_called_once_with("/rest/wlanconf")


class TestUniFiLocalClientAPGroupMethods:
    """Tests for AP group (broadcasting group) methods."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("ui_cli.local_client.settings") as mock:
            mock.controller_url = "https://192.168.1.1"
            mock.controller_username = "admin"
            mock.controller_password = "password"
            mock.controller_api_key = ""
            mock.controller_site = "default"
            mock.controller_verify_ssl = False
            mock.timeout = 30
            mock.session_file = MagicMock()
            mock.session_file.exists.return_value = False
            yield mock

    @pytest.fixture
    def mock_ap_groups_response(self):
        """Sample AP groups response."""
        return [
            {
                "_id": "group-001",
                "name": "All APs",
                "device_macs": ["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"],
                "attr_no_delete": True,
            },
            {
                "_id": "group-002",
                "name": "Office",
                "device_macs": ["aa:bb:cc:dd:ee:ff"],
            },
        ]

    @pytest.mark.asyncio
    async def test_get_ap_groups(self, mock_settings, mock_ap_groups_response):
        """Test getting AP groups."""
        client = UniFiLocalClient()

        with patch.object(
            client, "_v2_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_ap_groups_response

            groups = await client.get_ap_groups()

            assert len(groups) == 2
            assert groups[0]["name"] == "All APs"
            assert len(groups[0]["device_macs"]) == 2
            mock_request.assert_called_once_with("GET", "/apgroups")

    @pytest.mark.asyncio
    async def test_create_ap_group(self, mock_settings):
        """Test creating an AP group."""
        client = UniFiLocalClient()

        with patch.object(
            client, "_v2_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {
                "_id": "group-new",
                "name": "Test Group",
                "device_macs": [],
            }

            result = await client.create_ap_group("Test Group")

            assert result["name"] == "Test Group"
            mock_request.assert_called_once_with(
                "POST", "/apgroups", {"name": "Test Group", "device_macs": []}
            )

    @pytest.mark.asyncio
    async def test_create_ap_group_with_devices(self, mock_settings):
        """Test creating an AP group with devices."""
        client = UniFiLocalClient()

        with patch.object(
            client, "_v2_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {
                "_id": "group-new",
                "name": "Test Group",
                "device_macs": ["aa:bb:cc:dd:ee:ff"],
            }

            result = await client.create_ap_group(
                "Test Group", device_macs=["aa:bb:cc:dd:ee:ff"]
            )

            assert result["name"] == "Test Group"
            assert "aa:bb:cc:dd:ee:ff" in result["device_macs"]
            mock_request.assert_called_once_with(
                "POST",
                "/apgroups",
                {"name": "Test Group", "device_macs": ["aa:bb:cc:dd:ee:ff"]},
            )

    @pytest.mark.asyncio
    async def test_update_ap_group(self, mock_settings):
        """Test updating an AP group."""
        client = UniFiLocalClient()

        with patch.object(
            client, "_v2_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {
                "_id": "group-002",
                "name": "Updated Group",
                "device_macs": ["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"],
            }

            result = await client.update_ap_group(
                "group-002",
                "Updated Group",
                ["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"],
            )

            assert result["name"] == "Updated Group"
            assert len(result["device_macs"]) == 2
            mock_request.assert_called_once_with(
                "PUT",
                "/apgroups/group-002",
                {
                    "name": "Updated Group",
                    "device_macs": ["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"],
                },
            )

    @pytest.mark.asyncio
    async def test_delete_ap_group(self, mock_settings):
        """Test deleting an AP group."""
        client = UniFiLocalClient()

        with patch.object(
            client, "_v2_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = True

            result = await client.delete_ap_group("group-002")

            assert result is True
            mock_request.assert_called_once_with("DELETE", "/apgroups/group-002")


class TestLocalClientFormatting:
    """Tests for Local Controller data formatting helpers."""

    def test_device_status_online(self, mock_local_devices_response):
        """Test device status detection for online devices."""
        device = mock_local_devices_response[0]
        assert device["state"] == 1  # 1 = online

    def test_device_status_offline(self):
        """Test device status detection for offline devices."""
        device = {"state": 0}
        assert device["state"] == 0  # 0 = offline

    def test_client_is_wired(self, mock_local_clients_response):
        """Test client wired/wireless detection."""
        wired_client = mock_local_clients_response[1]
        wireless_client = mock_local_clients_response[0]
        assert wired_client["is_wired"] is True
        assert wireless_client["is_wired"] is False

    def test_voucher_code_format(self, mock_vouchers_response):
        """Test voucher code format."""
        voucher = mock_vouchers_response[0]
        code = voucher["code"]
        assert "-" in code
        assert len(code.replace("-", "")) == 10


class TestUniFiLocalClientApiKeyAuth:
    """Tests for API key authentication (AK1-AK6)."""

    @pytest.fixture
    def mock_settings_with_api_key(self):
        """Mock settings with API key configured."""
        with patch("ui_cli.local_client.settings") as mock:
            mock.controller_url = "https://192.168.1.1"
            mock.controller_username = ""
            mock.controller_password = ""
            mock.controller_api_key = "a" * 40  # 40-char hex API key
            mock.controller_site = "default"
            mock.controller_verify_ssl = False
            mock.timeout = 30
            mock.session_file = MagicMock()
            mock.session_file.exists.return_value = False
            yield mock

    @pytest.fixture
    def mock_settings_no_api_key(self):
        """Mock settings without API key (uses username/password)."""
        with patch("ui_cli.local_client.settings") as mock:
            mock.controller_url = "https://192.168.1.1"
            mock.controller_username = "admin"
            mock.controller_password = "password"
            mock.controller_api_key = ""
            mock.controller_site = "default"
            mock.controller_verify_ssl = False
            mock.timeout = 30
            mock.session_file = MagicMock()
            mock.session_file.exists.return_value = False
            yield mock

    # ---- AK1: X-API-KEY header sent on every request ----

    def test_ak1_api_key_sets_internal_attribute(self, mock_settings_with_api_key):
        """AK1: Client stores API key when UNIFI_CONTROLLER_API_KEY is set."""
        client = UniFiLocalClient()
        assert client._api_key == "a" * 40

    @pytest.mark.asyncio
    async def test_ak1_x_api_key_header_in_request(self, mock_settings_with_api_key):
        """AK1: X-API-KEY header is sent on every request when API key is set."""
        client = UniFiLocalClient()
        headers = client._get_headers()
        assert "X-API-KEY" in headers
        assert headers["X-API-KEY"] == "a" * 40

    @pytest.mark.asyncio
    async def test_ak1_no_csrf_token_in_api_key_mode(self, mock_settings_with_api_key):
        """AK1: X-CSRF-Token header is NOT included when using API key auth."""
        client = UniFiLocalClient()
        client._csrf_token = "some-csrf-token"  # Even if set, should not appear
        headers = client._get_headers()
        assert "X-CSRF-Token" not in headers
        assert "X-API-KEY" in headers

    @pytest.mark.asyncio
    async def test_ak1_request_uses_api_key_no_login(self, mock_settings_with_api_key):
        """AK1: When API key is set, _request() sends X-API-KEY without calling login()
        and uses the correct UDM URL prefix (/proxy/network/api/s/default/)."""
        client = UniFiLocalClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"meta": {"rc": "ok"}, "data": []}

        with patch("ui_cli.local_client.httpx.AsyncClient") as mock_client_cls, \
             patch.object(client, "login", new_callable=AsyncMock) as mock_login:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=None)
            mock_async_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_async_client

            await client.get("/stat/health")

            # login() must NOT be called when API key is set
            mock_login.assert_not_called()

            # Verify the actual call args passed to httpx
            call_kwargs = mock_async_client.request.call_args
            request_headers = call_kwargs.kwargs.get("headers", {})

            # X-API-KEY header must be present with the correct value
            assert "X-API-KEY" in request_headers
            assert request_headers["X-API-KEY"] == "a" * 40

            # URL must use the UDM proxy prefix, not the legacy /api/s/ path
            url = call_kwargs.kwargs.get("url", "")
            assert url.startswith("https://192.168.1.1/proxy/network/api/s/default/")

    # ---- AK2: Fallback to username/password when no API key ----

    def test_ak2_no_api_key_uses_username_password(self, mock_settings_no_api_key):
        """AK2: When no API key, client initializes with username/password."""
        client = UniFiLocalClient()
        assert client._api_key == ""
        assert client.username == "admin"
        assert client.password == "password"

    @pytest.mark.asyncio
    async def test_ak2_no_api_key_calls_login(self, mock_settings_no_api_key):
        """AK2: When no API key is set, ensure_authenticated() calls login()."""
        client = UniFiLocalClient()

        with patch.object(client, "_load_session", return_value=False), \
             patch.object(client, "login", new_callable=AsyncMock) as mock_login:
            await client.ensure_authenticated()
            mock_login.assert_called_once()

    # ---- AK3: Invalid API key → clear error, no silent fallback ----

    @pytest.mark.asyncio
    async def test_ak3_invalid_api_key_raises_auth_error(self, mock_settings_with_api_key):
        """AK3: 401 response with API key raises LocalAuthenticationError (no fallback)."""
        client = UniFiLocalClient()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("ui_cli.local_client.httpx.AsyncClient") as mock_client_cls:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=None)
            mock_async_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_async_client

            with pytest.raises(LocalAuthenticationError, match="API key rejected"):
                await client.get("/stat/health")

    @pytest.mark.asyncio
    async def test_ak3_invalid_api_key_does_not_fallback_to_login(self, mock_settings_with_api_key):
        """AK3: When API key returns 401, login() is NEVER called (no silent fallback)."""
        client = UniFiLocalClient()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("ui_cli.local_client.httpx.AsyncClient") as mock_client_cls, \
             patch.object(client, "login", new_callable=AsyncMock) as mock_login:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=None)
            mock_async_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_async_client

            with pytest.raises(LocalAuthenticationError):
                await client.get("/stat/health")

            mock_login.assert_not_called()

    @pytest.mark.asyncio
    async def test_ak3_v2_request_invalid_api_key_raises_auth_error(self, mock_settings_with_api_key):
        """AK3: 401 response via _v2_request with API key raises LocalAuthenticationError (no fallback)."""
        client = UniFiLocalClient()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.is_success = False

        with patch("ui_cli.local_client.httpx.AsyncClient") as mock_client_cls:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=None)
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_async_client

            with pytest.raises(LocalAuthenticationError, match="API key rejected"):
                await client.get_ap_groups()

    # ---- AK4: Settings field controller_api_key ----

    def test_ak4_settings_has_controller_api_key_field(self, monkeypatch):
        """AK4: Settings class has controller_api_key field."""
        from ui_cli.config import Settings
        # Isolate from real config files by overriding env vars
        monkeypatch.setenv("UNIFI_CONTROLLER_URL", "https://192.168.1.1")
        monkeypatch.setenv("UNIFI_CONTROLLER_USERNAME", "admin")
        monkeypatch.setenv("UNIFI_CONTROLLER_PASSWORD", "pass")
        monkeypatch.delenv("UNIFI_CONTROLLER_API_KEY", raising=False)
        s = Settings(_env_file=None)
        assert hasattr(s, "controller_api_key")
        assert s.controller_api_key == ""

    def test_ak4_controller_api_key_read_from_env(self, monkeypatch):
        """AK4: controller_api_key is read from UNIFI_CONTROLLER_API_KEY env var."""
        from ui_cli.config import Settings
        monkeypatch.setenv("UNIFI_CONTROLLER_API_KEY", "deadbeef" * 5)
        s = Settings(_env_file=None)
        assert s.controller_api_key == "deadbeef" * 5

    # ---- AK5: is_local_configured accepts API key OR username/password ----

    def test_ak5_is_local_configured_with_api_key(self, monkeypatch):
        """AK5: is_local_configured returns True when controller_url + api_key are set."""
        from ui_cli.config import Settings
        monkeypatch.setenv("UNIFI_CONTROLLER_URL", "https://192.168.1.1")
        monkeypatch.setenv("UNIFI_CONTROLLER_API_KEY", "a" * 40)
        monkeypatch.delenv("UNIFI_CONTROLLER_USERNAME", raising=False)
        monkeypatch.delenv("UNIFI_CONTROLLER_PASSWORD", raising=False)
        s = Settings(_env_file=None)
        assert s.is_local_configured is True

    def test_ak5_is_local_configured_with_username_password(self, monkeypatch):
        """AK5: is_local_configured returns True when controller_url + username + password are set."""
        from ui_cli.config import Settings
        monkeypatch.setenv("UNIFI_CONTROLLER_URL", "https://192.168.1.1")
        monkeypatch.setenv("UNIFI_CONTROLLER_USERNAME", "admin")
        monkeypatch.setenv("UNIFI_CONTROLLER_PASSWORD", "secret")
        monkeypatch.delenv("UNIFI_CONTROLLER_API_KEY", raising=False)
        s = Settings(_env_file=None)
        assert s.is_local_configured is True

    def test_ak5_is_local_configured_false_with_only_url(self, monkeypatch):
        """AK5: is_local_configured returns False when only controller_url is set."""
        from ui_cli.config import Settings
        monkeypatch.setenv("UNIFI_CONTROLLER_URL", "https://192.168.1.1")
        monkeypatch.delenv("UNIFI_CONTROLLER_USERNAME", raising=False)
        monkeypatch.delenv("UNIFI_CONTROLLER_PASSWORD", raising=False)
        monkeypatch.delenv("UNIFI_CONTROLLER_API_KEY", raising=False)
        s = Settings(_env_file=None)
        assert s.is_local_configured is False

    def test_ak5_is_local_configured_false_without_url(self, monkeypatch):
        """AK5: is_local_configured returns False when controller_url is missing."""
        from ui_cli.config import Settings
        monkeypatch.delenv("UNIFI_CONTROLLER_URL", raising=False)
        monkeypatch.setenv("UNIFI_CONTROLLER_API_KEY", "a" * 40)
        s = Settings(_env_file=None)
        assert s.is_local_configured is False

    # ---- AK6: init validation skips username/password check when API key set ----

    def test_ak6_init_without_credentials_succeeds_when_api_key_set(self, mock_settings_with_api_key):
        """AK6: Client __init__ does NOT raise when api_key is set and credentials are empty."""
        # Should NOT raise LocalAuthenticationError about missing credentials
        client = UniFiLocalClient()
        assert client._api_key == "a" * 40
