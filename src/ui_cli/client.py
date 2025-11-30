"""Async HTTP client for UniFi Site Manager API."""

from typing import Any

import httpx

from ui_cli.config import settings


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(APIError):
    """Raised when API key is invalid or missing."""

    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class UniFiClient:
    """Async client for UniFi Site Manager API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ):
        self.api_key = api_key or settings.api_key
        self.base_url = (base_url or settings.api_url).rstrip("/")
        self.timeout = timeout or settings.timeout

        if not self.api_key:
            raise AuthenticationError(
                "API key not configured. Set UNIFI_API_KEY environment variable or create a .env file."
            )

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        return {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to the API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
            )

            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key", status_code=401)
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None,
                )
            elif response.status_code >= 400:
                raise APIError(
                    f"API error: {response.text}",
                    status_code=response.status_code,
                )

            return response.json()

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, params=params)

    # ========== Hosts ==========

    async def list_hosts(self) -> list[dict[str, Any]]:
        """List all hosts associated with the account."""
        response = await self.get("/hosts")
        return response.get("data", [])

    async def get_host(self, host_id: str) -> dict[str, Any]:
        """Get details for a specific host."""
        response = await self.get(f"/hosts/{host_id}")
        return response.get("data", {})

    # ========== Sites ==========

    async def list_sites(self) -> list[dict[str, Any]]:
        """List all sites."""
        response = await self.get("/sites")
        return response.get("data", [])

    # ========== Devices ==========

    async def list_devices_raw(
        self,
        host_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List all devices grouped by host (raw API response)."""
        params = {}
        if host_ids:
            params["hostIds[]"] = host_ids
        response = await self.get("/devices", params=params if params else None)
        return response.get("data", [])

    async def list_devices(
        self,
        host_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List all devices, flattened with host info included."""
        raw_data = await self.list_devices_raw(host_ids=host_ids)

        # Flatten: API returns devices grouped by host
        devices = []
        for host_group in raw_data:
            host_id = host_group.get("hostId", "")
            host_name = host_group.get("hostName", "")
            for device in host_group.get("devices", []):
                # Add host info to each device
                device["hostId"] = host_id
                device["hostName"] = host_name
                devices.append(device)

        return devices

    # ========== ISP Metrics (Early Access API) ==========

    async def get_isp_metrics(
        self,
        metric_type: str = "1h",
        duration_hours: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get ISP metrics.

        Args:
            metric_type: Either '5m' (24h retention) or '1h' (30d retention)
            duration_hours: Hours of data to retrieve. Defaults to 24 for 5m, 168 (7 days) for 1h

        Note: Uses Early Access API endpoint (/ea/)
        """
        from datetime import datetime, timedelta, timezone

        # Set default duration based on metric type
        if duration_hours is None:
            duration_hours = 24 if metric_type == "5m" else 168  # 7 days for hourly

        # Calculate timestamps
        end_time = datetime.now(timezone.utc)
        begin_time = end_time - timedelta(hours=duration_hours)

        params = {
            "beginTimestamp": begin_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endTimestamp": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        # ISP metrics uses EA endpoint, not v1
        ea_url = self.base_url.replace("/v1", "/ea")
        url = f"{ea_url}/isp-metrics/{metric_type}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._get_headers(), params=params)

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key", status_code=401)
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None,
                )
            elif response.status_code >= 400:
                raise APIError(
                    f"API error: {response.text}",
                    status_code=response.status_code,
                )

            raw_data = response.json().get("data", [])

            # Flatten the nested structure
            metrics = []
            for site_data in raw_data:
                site_id = site_data.get("siteId", "")
                host_id = site_data.get("hostId", "")
                for period in site_data.get("periods", []):
                    wan_data = period.get("data", {}).get("wan", {})
                    metrics.append({
                        "siteId": site_id,
                        "hostId": host_id,
                        "timestamp": period.get("metricTime", ""),
                        "avgLatency": wan_data.get("avgLatency"),
                        "maxLatency": wan_data.get("maxLatency"),
                        "downloadKbps": wan_data.get("download_kbps"),
                        "uploadKbps": wan_data.get("upload_kbps"),
                        "uptime": wan_data.get("uptime"),
                        "downtime": wan_data.get("downtime"),
                        "packetLoss": wan_data.get("packetLoss"),
                        "ispName": wan_data.get("ispName"),
                        "ispAsn": wan_data.get("ispAsn"),
                    })

            return metrics

    # ========== SD-WAN (Early Access API) ==========

    async def _ea_get(self, endpoint: str) -> dict[str, Any]:
        """Make a GET request to the Early Access API."""
        ea_url = self.base_url.replace("/v1", "/ea")
        url = f"{ea_url}/{endpoint.lstrip('/')}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._get_headers())

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key", status_code=401)
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None,
                )
            elif response.status_code >= 400:
                raise APIError(
                    f"API error: {response.text}",
                    status_code=response.status_code,
                )

            return response.json()

    async def list_sdwan_configs(self) -> list[dict[str, Any]]:
        """List all SD-WAN configurations."""
        response = await self._ea_get("/sd-wan-configs")
        return response.get("data", [])

    async def get_sdwan_config(self, config_id: str) -> dict[str, Any]:
        """Get details for a specific SD-WAN configuration."""
        response = await self._ea_get(f"/sd-wan-configs/{config_id}")
        return response.get("data", {})

    async def get_sdwan_status(self, config_id: str) -> dict[str, Any]:
        """Get deployment status for a specific SD-WAN configuration."""
        response = await self._ea_get(f"/sd-wan-configs/{config_id}/status")
        return response.get("data", {})
