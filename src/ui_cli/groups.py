"""Client groups management for ui-cli.

Groups allow users to organize client devices and perform bulk actions.
Supports both static (manual membership) and auto (rule-based) groups.

Storage: ~/.config/ui-cli/groups.json
"""

from pathlib import Path
from datetime import datetime, timezone
from typing import Literal
import json
import re
import fnmatch
from pydantic import BaseModel


class GroupMember(BaseModel):
    """A member of a static group."""

    mac: str
    alias: str | None = None


class AutoGroupRules(BaseModel):
    """Rules for auto group membership evaluation."""

    vendor: list[str] | None = None  # OUI/manufacturer patterns
    name: list[str] | None = None  # Client name patterns
    hostname: list[str] | None = None  # Hostname patterns
    network: list[str] | None = None  # Network/SSID patterns
    ip: list[str] | None = None  # IP address patterns/ranges
    mac: list[str] | None = None  # MAC prefix patterns
    conn_type: list[str] | None = None  # "wired" or "wireless"


class Group(BaseModel):
    """A client group definition."""

    name: str
    description: str | None = None
    type: Literal["static", "auto"] = "static"
    members: list[GroupMember] | None = None  # For static groups
    rules: AutoGroupRules | None = None  # For auto groups
    created_at: datetime
    updated_at: datetime


class GroupsFile(BaseModel):
    """Root structure for groups.json file."""

    version: int = 1
    groups: dict[str, Group] = {}


class GroupManager:
    """Manages client groups stored in ~/.config/ui-cli/groups.json"""

    def __init__(self):
        self._path = Path.home() / ".config" / "ui-cli" / "groups.json"
        self._data: GroupsFile | None = None

    @property
    def data(self) -> GroupsFile:
        """Lazy-load groups data."""
        if self._data is None:
            self._load()
        return self._data

    def _load(self) -> None:
        """Load groups from disk."""
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text())
                self._data = GroupsFile(**raw)
            except (json.JSONDecodeError, ValueError):
                # Corrupted file, start fresh
                self._data = GroupsFile()
        else:
            self._data = GroupsFile()

    def _save(self) -> None:
        """Save groups to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self.data.model_dump(), indent=2, default=str)
        )

    @staticmethod
    def slugify(name: str) -> str:
        """Convert display name to slug.

        Example: 'Kids Devices' -> 'kids-devices'
        """
        slug = name.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")

    @staticmethod
    def normalize_mac(mac: str) -> str:
        """Normalize MAC address to uppercase with colons.

        Handles formats:
        - AA:BB:CC:DD:EE:FF
        - AA-BB-CC-DD-EE-FF
        - AABBCCDDEEFF
        - aa:bb:cc:dd:ee:ff
        """
        mac = mac.upper().replace("-", ":").replace(".", ":")
        # Handle formats like AABBCCDDEEFF
        if ":" not in mac and len(mac) == 12:
            mac = ":".join(mac[i : i + 2] for i in range(0, 12, 2))
        return mac

    def _resolve_group(self, name_or_slug: str) -> str | None:
        """Resolve name or slug to slug, return None if not found."""
        slug = self.slugify(name_or_slug)
        if slug in self.data.groups:
            return slug
        # Try exact name match
        for s, g in self.data.groups.items():
            if g.name.lower() == name_or_slug.lower():
                return s
        return None

    # -------------------------------------------------------------------------
    # Group CRUD
    # -------------------------------------------------------------------------

    def list_groups(self) -> list[tuple[str, Group]]:
        """List all groups as (slug, Group) tuples."""
        return list(self.data.groups.items())

    def get_group(self, name_or_slug: str) -> tuple[str, Group] | None:
        """Get group by name or slug.

        Returns (slug, Group) or None if not found.
        """
        slug = self._resolve_group(name_or_slug)
        if slug:
            return (slug, self.data.groups[slug])
        return None

    def create_group(
        self,
        name: str,
        description: str | None = None,
        group_type: Literal["static", "auto"] = "static",
        rules: AutoGroupRules | None = None,
    ) -> tuple[str, Group]:
        """Create a new group.

        Returns (slug, Group).
        Raises ValueError if group already exists.
        """
        slug = self.slugify(name)
        if slug in self.data.groups:
            raise ValueError(f"Group '{name}' already exists")

        now = datetime.now(timezone.utc)
        group = Group(
            name=name,
            description=description,
            type=group_type,
            members=[] if group_type == "static" else None,
            rules=rules if group_type == "auto" else None,
            created_at=now,
            updated_at=now,
        )
        self.data.groups[slug] = group
        self._save()
        return (slug, group)

    def delete_group(self, name_or_slug: str) -> bool:
        """Delete a group.

        Returns True if deleted, False if not found.
        """
        slug = self._resolve_group(name_or_slug)
        if not slug:
            return False
        del self.data.groups[slug]
        self._save()
        return True

    def update_group(
        self,
        name_or_slug: str,
        new_name: str | None = None,
        description: str | None = ...,  # type: ignore  # Use ... to distinguish from None
    ) -> tuple[str, Group]:
        """Update group name and/or description.

        Returns (slug, Group).
        Raises ValueError if group not found.
        """
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]

        # Handle rename (may change slug)
        if new_name:
            group.name = new_name
            new_slug = self.slugify(new_name)
            if new_slug != slug:
                self.data.groups[new_slug] = group
                del self.data.groups[slug]
                slug = new_slug

        # Handle description update (... means not provided)
        if description is not ...:
            group.description = description

        group.updated_at = datetime.now(timezone.utc)
        self._save()
        return (slug, group)

    # -------------------------------------------------------------------------
    # Member CRUD Operations (Static Groups)
    # -------------------------------------------------------------------------

    def add_member(
        self,
        name_or_slug: str,
        mac: str,
        alias: str | None = None,
    ) -> Group:
        """Add a member to a static group.

        If member already exists, updates the alias if provided.
        Raises ValueError if group not found or is auto group.
        """
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static":
            raise ValueError("Cannot add members to auto groups")

        mac = self.normalize_mac(mac)

        # Check if already exists - update alias if so
        if group.members:
            for member in group.members:
                if member.mac == mac:
                    if alias:
                        member.alias = alias
                        group.updated_at = datetime.now(timezone.utc)
                    self._save()
                    return group

        # Add new member
        if group.members is None:
            group.members = []
        group.members.append(GroupMember(mac=mac, alias=alias))
        group.updated_at = datetime.now(timezone.utc)
        self._save()
        return group

    def get_member(self, name_or_slug: str, identifier: str) -> GroupMember | None:
        """Get a member by MAC or alias.

        Returns GroupMember or None if not found.
        """
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static" or not group.members:
            return None

        identifier_mac = self.normalize_mac(identifier)
        for member in group.members:
            if member.mac == identifier_mac or member.alias == identifier:
                return member
        return None

    def update_member(
        self,
        name_or_slug: str,
        identifier: str,
        alias: str | None = ...,  # type: ignore
    ) -> bool:
        """Update a member's alias.

        Pass alias=None to clear the alias.
        Returns True if updated, False if member not found.
        """
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static" or not group.members:
            return False

        identifier_mac = self.normalize_mac(identifier)
        for member in group.members:
            if member.mac == identifier_mac or member.alias == identifier:
                if alias is not ...:
                    member.alias = alias
                group.updated_at = datetime.now(timezone.utc)
                self._save()
                return True
        return False

    def remove_member(self, name_or_slug: str, identifier: str) -> bool:
        """Remove a member by MAC or alias.

        Returns True if removed, False if not found.
        """
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static" or not group.members:
            return False

        identifier_mac = self.normalize_mac(identifier)
        for i, member in enumerate(group.members):
            if member.mac == identifier_mac or member.alias == identifier:
                group.members.pop(i)
                group.updated_at = datetime.now(timezone.utc)
                self._save()
                return True
        return False

    def list_members(self, name_or_slug: str) -> list[GroupMember]:
        """List all members in a static group.

        Raises ValueError if group not found or is auto group.
        """
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static":
            raise ValueError("Auto groups have dynamic membership")
        return group.members or []

    def clear_members(self, name_or_slug: str) -> bool:
        """Clear all members from a static group.

        Raises ValueError if group not found or is auto group.
        """
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "static":
            raise ValueError("Cannot clear members from auto groups")

        group.members = []
        group.updated_at = datetime.now(timezone.utc)
        self._save()
        return True

    def get_member_macs(self, name_or_slug: str) -> list[str]:
        """Get list of MAC addresses in a static group."""
        result = self.get_group(name_or_slug)
        if not result:
            raise ValueError(f"Group '{name_or_slug}' not found")
        _, group = result
        if group.type != "static" or not group.members:
            return []
        return [m.mac for m in group.members]

    # -------------------------------------------------------------------------
    # Auto Group Operations
    # -------------------------------------------------------------------------

    def set_rules(self, name_or_slug: str, rules: AutoGroupRules) -> Group:
        """Set rules for an auto group.

        Raises ValueError if group not found or is static group.
        """
        slug = self._resolve_group(name_or_slug)
        if not slug:
            raise ValueError(f"Group '{name_or_slug}' not found")

        group = self.data.groups[slug]
        if group.type != "auto":
            raise ValueError("Cannot set rules on static groups")

        group.rules = rules
        group.updated_at = datetime.now(timezone.utc)
        self._save()
        return group

    @staticmethod
    def pattern_matches(pattern: str, value: str | None) -> bool:
        """Check if value matches pattern.

        Pattern syntax:
        - Exact: "Apple" - case-insensitive exact match
        - Wildcard: "*phone*" - uses fnmatch
        - Regex: "~^iPhone-[0-9]+" - prefix with ~ for regex
        - Multiple: "Apple,Samsung" - comma-separated, OR logic
        """
        if not pattern or not value:
            return False

        # Handle multiple patterns (OR logic)
        if "," in pattern and not pattern.startswith("~"):
            patterns = [p.strip() for p in pattern.split(",")]
            return any(GroupManager.pattern_matches(p, value) for p in patterns)

        # Regex pattern (prefix with ~)
        if pattern.startswith("~"):
            try:
                return bool(re.search(pattern[1:], value, re.IGNORECASE))
            except re.error:
                return False

        # Wildcard pattern
        if "*" in pattern or "?" in pattern:
            return fnmatch.fnmatch(value.lower(), pattern.lower())

        # Exact match (case-insensitive)
        return value.lower() == pattern.lower()

    @staticmethod
    def ip_matches(pattern: str, ip: str | None) -> bool:
        """Check if IP matches pattern.

        Supports:
        - CIDR: 192.168.1.0/24
        - Range: 192.168.1.100-200 or 192.168.1.100-192.168.1.200
        - Wildcard: 192.168.1.*
        """
        if not pattern or not ip:
            return False

        import ipaddress

        # CIDR notation: 192.168.1.0/24
        if "/" in pattern:
            try:
                network = ipaddress.ip_network(pattern, strict=False)
                return ipaddress.ip_address(ip) in network
            except ValueError:
                return False

        # Range: 192.168.1.100-200
        if "-" in pattern and not pattern.startswith("-"):
            try:
                base, end = pattern.rsplit("-", 1)
                if "." in end:
                    # Full IP range: 192.168.1.100-192.168.1.200
                    start_ip = ipaddress.ip_address(base)
                    end_ip = ipaddress.ip_address(end)
                else:
                    # Partial range: 192.168.1.100-200
                    start_ip = ipaddress.ip_address(base)
                    base_parts = base.rsplit(".", 1)
                    end_ip = ipaddress.ip_address(f"{base_parts[0]}.{end}")
                target = ipaddress.ip_address(ip)
                return start_ip <= target <= end_ip
            except ValueError:
                return False

        # Wildcard: 192.168.1.*
        return GroupManager.pattern_matches(pattern, ip)

    def evaluate_auto_group(
        self,
        name_or_slug: str,
        clients: list[dict],
    ) -> list[dict]:
        """Evaluate auto group rules against client list.

        Returns list of matching clients.
        Raises ValueError if group not found.
        """
        result = self.get_group(name_or_slug)
        if not result:
            raise ValueError(f"Group '{name_or_slug}' not found")

        _, group = result
        if group.type != "auto" or not group.rules:
            return []

        matching = []
        for client in clients:
            if self._client_matches_rules(client, group.rules):
                matching.append(client)
        return matching

    def _client_matches_rules(self, client: dict, rules: AutoGroupRules) -> bool:
        """Check if client matches all rules (AND logic between rule types)."""
        # Vendor (OUI)
        if rules.vendor:
            oui = client.get("oui", "")
            if not any(self.pattern_matches(p, oui) for p in rules.vendor):
                return False

        # Client name
        if rules.name:
            name = client.get("name") or client.get("hostname") or ""
            if not any(self.pattern_matches(p, name) for p in rules.name):
                return False

        # Hostname
        if rules.hostname:
            hostname = client.get("hostname", "")
            if not any(self.pattern_matches(p, hostname) for p in rules.hostname):
                return False

        # Network/SSID
        if rules.network:
            network = client.get("essid") or client.get("network", "")
            if not any(self.pattern_matches(p, network) for p in rules.network):
                return False

        # IP address
        if rules.ip:
            ip = client.get("ip", "")
            if not any(self.ip_matches(p, ip) for p in rules.ip):
                return False

        # MAC prefix
        if rules.mac:
            mac = client.get("mac", "")
            if not any(mac.upper().startswith(p.upper().replace("-", ":")) for p in rules.mac):
                return False

        # Connection type
        if rules.conn_type:
            is_wired = client.get("is_wired", False)
            client_type = "wired" if is_wired else "wireless"
            if client_type not in [t.lower() for t in rules.conn_type]:
                return False

        return True

    # -------------------------------------------------------------------------
    # Import/Export
    # -------------------------------------------------------------------------

    def export_groups(self) -> dict:
        """Export all groups as dict."""
        return self.data.model_dump()

    def import_groups(self, data: dict, replace: bool = False) -> int:
        """Import groups from dict.

        Args:
            data: Groups data to import
            replace: If True, replace all existing groups. If False, merge.

        Returns count of imported groups.
        """
        imported = GroupsFile(**data)
        if replace:
            self._data = imported
        else:
            for slug, group in imported.groups.items():
                self.data.groups[slug] = group
        self._save()
        return len(imported.groups)
