"""Pydantic models for UniFi API responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ========== Host Models ==========


class HostReportedState(BaseModel):
    """Host reported state information."""

    hostname: str | None = None
    version: str | None = None
    hardware_id: str | None = Field(None, alias="hardwareId")
    firmware_version: str | None = Field(None, alias="firmwareVersion")
    ip_address: str | None = Field(None, alias="ipAddress")
    mac_address: str | None = Field(None, alias="macAddress")

    class Config:
        populate_by_name = True


class Host(BaseModel):
    """UniFi host (console/controller) model."""

    id: str
    hardware_id: str | None = Field(None, alias="hardwareId")
    type: str | None = None
    ip_address: str | None = Field(None, alias="ipAddress")
    is_blocked: bool | None = Field(None, alias="isBlocked")
    last_connection_state_change: datetime | None = Field(
        None, alias="lastConnectionStateChange"
    )
    latest_backup_time: datetime | None = Field(None, alias="latestBackupTime")
    registration_time: datetime | None = Field(None, alias="registrationTime")
    owner: bool | None = None
    reported_state: HostReportedState | None = Field(None, alias="reportedState")
    user_data: dict[str, Any] | None = Field(None, alias="userData")

    class Config:
        populate_by_name = True


# ========== Site Models ==========


class SiteMeta(BaseModel):
    """Site metadata."""

    name: str | None = None
    desc: str | None = None
    timezone: str | None = None
    gateway_mac: str | None = Field(None, alias="gatewayMac")

    class Config:
        populate_by_name = True


class SiteStatistics(BaseModel):
    """Site statistics."""

    counts: dict[str, int] | None = None

    class Config:
        populate_by_name = True


class Site(BaseModel):
    """UniFi site model."""

    site_id: str | None = Field(None, alias="siteId")
    host_id: str | None = Field(None, alias="hostId")
    is_owner: bool | None = Field(None, alias="isOwner")
    permission: str | None = None
    meta: SiteMeta | None = None
    statistics: SiteStatistics | None = None
    subscription_end_time: datetime | None = Field(None, alias="subscriptionEndTime")

    class Config:
        populate_by_name = True


# ========== Device Models ==========


class DeviceUidb(BaseModel):
    """Device UIDB (database) information."""

    id: str | None = None
    guid: str | None = None
    images: dict[str, Any] | None = None

    class Config:
        populate_by_name = True


class Device(BaseModel):
    """UniFi device model."""

    id: str
    mac: str | None = None
    name: str | None = None
    model: str | None = None
    shortname: str | None = None
    ip: str | None = None
    product_line: str | None = Field(None, alias="productLine")
    status: str | None = None
    version: str | None = None
    firmware_status: str | None = Field(None, alias="firmwareStatus")
    is_console: bool | None = Field(None, alias="isConsole")
    is_managed: bool | None = Field(None, alias="isManaged")
    startup_time: datetime | None = Field(None, alias="startupTime")
    adoption_time: datetime | None = Field(None, alias="adoptionTime")
    host_id: str | None = Field(None, alias="hostId")
    host_name: str | None = Field(None, alias="hostName")
    updated_at: datetime | None = Field(None, alias="updatedAt")
    uidb: DeviceUidb | None = None

    class Config:
        populate_by_name = True


# ========== ISP Metrics Models ==========


class ISPMetric(BaseModel):
    """ISP performance metric model."""

    site_id: str | None = Field(None, alias="siteId")
    host_id: str | None = Field(None, alias="hostId")
    timestamp: datetime | None = None
    avg_latency: float | None = Field(None, alias="avgLatency")
    max_latency: float | None = Field(None, alias="maxLatency")
    download_kbps: float | None = Field(None, alias="downloadKbps")
    upload_kbps: float | None = Field(None, alias="uploadKbps")
    uptime: float | None = None
    downtime: float | None = None
    packet_loss: float | None = Field(None, alias="packetLoss")
    isp_name: str | None = Field(None, alias="ispName")
    isp_asn: str | None = Field(None, alias="ispAsn")

    class Config:
        populate_by_name = True


# ========== SD-WAN Models ==========


class SDWanSettings(BaseModel):
    """SD-WAN configuration settings."""

    hubs_interconnect: bool | None = Field(None, alias="hubsInterconnect")
    spoke_to_hub_tunnels_mode: str | None = Field(None, alias="spokeToHubTunnelsMode")
    spokes_auto_scale_and_nat_enabled: bool | None = Field(
        None, alias="spokesAutoScaleAndNatEnabled"
    )

    class Config:
        populate_by_name = True


class SDWanConfig(BaseModel):
    """SD-WAN configuration model."""

    id: str
    name: str | None = None
    type: str | None = None
    variant: str | None = None
    settings: SDWanSettings | None = None

    class Config:
        populate_by_name = True


class SDWanStatus(BaseModel):
    """SD-WAN deployment status model."""

    fingerprint: str | None = None
    updated_at: datetime | None = Field(None, alias="updatedAt")
    status: str | None = None
    progress: float | None = None
    errors: list[str] | None = None

    class Config:
        populate_by_name = True
