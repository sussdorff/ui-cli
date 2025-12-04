"""Unit tests for client groups functionality."""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from ui_cli.groups import (
    GroupManager,
    Group,
    GroupMember,
    AutoGroupRules,
    GroupsFile,
)


class TestGroupMember:
    """Tests for GroupMember model."""

    def test_create_member_with_mac(self):
        """Test creating a member with just MAC address."""
        member = GroupMember(mac="AA:BB:CC:DD:EE:FF")
        assert member.mac == "AA:BB:CC:DD:EE:FF"
        assert member.alias is None

    def test_create_member_with_alias(self):
        """Test creating a member with MAC and alias."""
        member = GroupMember(mac="AA:BB:CC:DD:EE:FF", alias="My Device")
        assert member.mac == "AA:BB:CC:DD:EE:FF"
        assert member.alias == "My Device"


class TestAutoGroupRules:
    """Tests for AutoGroupRules model."""

    def test_create_rules_with_vendor(self):
        """Test creating rules with vendor filter."""
        rules = AutoGroupRules(vendor=["Apple", "Samsung"])
        assert rules.vendor == ["Apple", "Samsung"]
        assert rules.name is None

    def test_create_rules_multiple_types(self):
        """Test creating rules with multiple filter types."""
        rules = AutoGroupRules(
            vendor=["Apple"],
            network=["Guest"],
            conn_type=["wireless"],
        )
        assert rules.vendor == ["Apple"]
        assert rules.network == ["Guest"]
        assert rules.conn_type == ["wireless"]


class TestGroup:
    """Tests for Group model."""

    def test_create_static_group(self):
        """Test creating a static group."""
        now = datetime.now(timezone.utc)
        group = Group(name="Kids Devices", type="static", created_at=now, updated_at=now)
        assert group.name == "Kids Devices"
        assert group.type == "static"
        assert group.members is None
        assert group.rules is None

    def test_create_auto_group(self):
        """Test creating an auto group with rules."""
        now = datetime.now(timezone.utc)
        rules = AutoGroupRules(vendor=["Apple"])
        group = Group(name="Apple Devices", type="auto", rules=rules, created_at=now, updated_at=now)
        assert group.name == "Apple Devices"
        assert group.type == "auto"
        assert group.rules.vendor == ["Apple"]


class TestGroupManager:
    """Tests for GroupManager class."""

    @pytest.fixture
    def group_manager(self, tmp_path):
        """Create a GroupManager with temporary storage."""
        groups_file = tmp_path / "groups.json"
        gm = GroupManager()
        gm._path = groups_file
        return gm

    def test_create_static_group(self, group_manager):
        """Test creating a static group."""
        slug, group = group_manager.create_group("Kids Devices", "Tablets and phones")

        assert slug == "kids-devices"
        assert group.name == "Kids Devices"
        assert group.description == "Tablets and phones"
        assert group.type == "static"

    def test_create_auto_group(self, group_manager):
        """Test creating an auto group."""
        rules = AutoGroupRules(vendor=["Apple"])
        slug, group = group_manager.create_group(
            "Apple Devices",
            "All Apple products",
            "auto",
            rules
        )

        assert slug == "apple-devices"
        assert group.name == "Apple Devices"
        assert group.type == "auto"
        assert group.rules.vendor == ["Apple"]

    def test_create_duplicate_group_fails(self, group_manager):
        """Test that creating a duplicate group raises error."""
        group_manager.create_group("Test Group")

        with pytest.raises(ValueError, match="already exists"):
            group_manager.create_group("Test Group")

    def test_get_group_by_slug(self, group_manager):
        """Test getting a group by slug."""
        group_manager.create_group("My Test Group")

        result = group_manager.get_group("my-test-group")
        assert result is not None
        slug, group = result
        assert slug == "my-test-group"
        assert group.name == "My Test Group"

    def test_get_group_by_name(self, group_manager):
        """Test getting a group by name."""
        group_manager.create_group("My Test Group")

        result = group_manager.get_group("My Test Group")
        assert result is not None
        slug, group = result
        assert group.name == "My Test Group"

    def test_get_nonexistent_group(self, group_manager):
        """Test getting a group that doesn't exist."""
        result = group_manager.get_group("nonexistent")
        assert result is None

    def test_list_groups(self, group_manager):
        """Test listing all groups."""
        group_manager.create_group("Group A")
        group_manager.create_group("Group B")

        groups = group_manager.list_groups()
        assert len(groups) == 2
        names = [g[1].name for g in groups]
        assert "Group A" in names
        assert "Group B" in names

    def test_delete_group(self, group_manager):
        """Test deleting a group."""
        group_manager.create_group("To Delete")

        result = group_manager.delete_group("to-delete")
        assert result is True
        assert group_manager.get_group("to-delete") is None

    def test_delete_nonexistent_group(self, group_manager):
        """Test deleting a group that doesn't exist."""
        result = group_manager.delete_group("nonexistent")
        assert result is False

    def test_update_group(self, group_manager):
        """Test updating a group's name and description."""
        group_manager.create_group("Original Name", "Original desc")

        slug, group = group_manager.update_group(
            "original-name",
            new_name="New Name",
            description="New desc"
        )

        assert group.name == "New Name"
        assert group.description == "New desc"

    def test_add_member(self, group_manager):
        """Test adding a member to a static group."""
        group_manager.create_group("Test Group")

        group = group_manager.add_member("test-group", "AA:BB:CC:DD:EE:FF", "My Device")

        assert len(group.members) == 1
        assert group.members[0].mac == "AA:BB:CC:DD:EE:FF"
        assert group.members[0].alias == "My Device"

    def test_add_duplicate_member_updates_alias(self, group_manager):
        """Test that adding a duplicate member updates the alias."""
        group_manager.create_group("Test Group")
        group_manager.add_member("test-group", "AA:BB:CC:DD:EE:FF", "Original")

        # Adding same MAC with new alias should update it
        group = group_manager.add_member("test-group", "AA:BB:CC:DD:EE:FF", "Updated")

        assert len(group.members) == 1
        assert group.members[0].alias == "Updated"

    def test_add_member_to_auto_group_fails(self, group_manager):
        """Test that adding a member to auto group raises error."""
        rules = AutoGroupRules(vendor=["Apple"])
        group_manager.create_group("Auto Group", group_type="auto", rules=rules)

        with pytest.raises(ValueError, match="Cannot add members to auto groups"):
            group_manager.add_member("auto-group", "AA:BB:CC:DD:EE:FF")

    def test_remove_member_by_mac(self, group_manager):
        """Test removing a member by MAC address."""
        group_manager.create_group("Test Group")
        group_manager.add_member("test-group", "AA:BB:CC:DD:EE:FF")

        result = group_manager.remove_member("test-group", "AA:BB:CC:DD:EE:FF")

        assert result is True
        _, group = group_manager.get_group("test-group")
        assert len(group.members) == 0

    def test_remove_member_by_alias(self, group_manager):
        """Test removing a member by alias."""
        group_manager.create_group("Test Group")
        group_manager.add_member("test-group", "AA:BB:CC:DD:EE:FF", "My Device")

        result = group_manager.remove_member("test-group", "My Device")

        assert result is True

    def test_clear_members(self, group_manager):
        """Test clearing all members from a group."""
        group_manager.create_group("Test Group")
        group_manager.add_member("test-group", "AA:BB:CC:DD:EE:FF")
        group_manager.add_member("test-group", "11:22:33:44:55:66")

        group_manager.clear_members("test-group")

        _, group = group_manager.get_group("test-group")
        assert len(group.members) == 0

    def test_list_members(self, group_manager):
        """Test listing members of a group."""
        group_manager.create_group("Test Group")
        group_manager.add_member("test-group", "AA:BB:CC:DD:EE:FF", "Device A")
        group_manager.add_member("test-group", "11:22:33:44:55:66", "Device B")

        members = group_manager.list_members("test-group")

        assert len(members) == 2
        aliases = [m.alias for m in members]
        assert "Device A" in aliases
        assert "Device B" in aliases


class TestPatternMatching:
    """Tests for pattern matching in auto groups."""

    def test_exact_match(self):
        """Test exact pattern matching."""
        assert GroupManager.pattern_matches("Apple", "Apple") is True
        assert GroupManager.pattern_matches("Apple", "apple") is True  # Case insensitive
        assert GroupManager.pattern_matches("Apple", "Samsung") is False

    def test_wildcard_contains(self):
        """Test wildcard contains matching."""
        assert GroupManager.pattern_matches("*phone*", "iPhone") is True
        assert GroupManager.pattern_matches("*phone*", "Android Phone") is True
        assert GroupManager.pattern_matches("*phone*", "Tablet") is False

    def test_wildcard_prefix(self):
        """Test wildcard prefix matching."""
        assert GroupManager.pattern_matches("iPhone*", "iPhone") is True
        assert GroupManager.pattern_matches("iPhone*", "iPhone-12") is True
        assert GroupManager.pattern_matches("iPhone*", "My iPhone") is False

    def test_wildcard_suffix(self):
        """Test wildcard suffix matching."""
        assert GroupManager.pattern_matches("*-TV", "Living-TV") is True
        assert GroupManager.pattern_matches("*-TV", "Bedroom-TV") is True
        assert GroupManager.pattern_matches("*-TV", "TV-Stand") is False

    def test_regex_pattern(self):
        """Test regex pattern matching."""
        assert GroupManager.pattern_matches("~^iPhone-[0-9]+$", "iPhone-12") is True
        assert GroupManager.pattern_matches("~^iPhone-[0-9]+$", "iPhone-1") is True
        assert GroupManager.pattern_matches("~^iPhone-[0-9]+$", "iPhoneXR") is False

    def test_comma_separated_or(self):
        """Test comma-separated OR matching."""
        assert GroupManager.pattern_matches("Apple,Samsung", "Apple") is True
        assert GroupManager.pattern_matches("Apple,Samsung", "Samsung") is True
        assert GroupManager.pattern_matches("Apple,Samsung", "Google") is False


class TestMACNormalization:
    """Tests for MAC address normalization."""

    def test_normalize_colons(self):
        """Test normalizing MAC with colons."""
        result = GroupManager.normalize_mac("aa:bb:cc:dd:ee:ff")
        assert result == "AA:BB:CC:DD:EE:FF"

    def test_normalize_hyphens(self):
        """Test normalizing MAC with hyphens."""
        result = GroupManager.normalize_mac("aa-bb-cc-dd-ee-ff")
        assert result == "AA:BB:CC:DD:EE:FF"

    def test_normalize_no_separator(self):
        """Test normalizing MAC without separators."""
        result = GroupManager.normalize_mac("aabbccddeeff")
        assert result == "AA:BB:CC:DD:EE:FF"

    def test_already_normalized(self):
        """Test already normalized MAC stays the same."""
        result = GroupManager.normalize_mac("AA:BB:CC:DD:EE:FF")
        assert result == "AA:BB:CC:DD:EE:FF"


class TestSlugGeneration:
    """Tests for slug generation."""

    def test_simple_name(self):
        """Test slug from simple name."""
        result = GroupManager.slugify("Kids Devices")
        assert result == "kids-devices"

    def test_special_characters(self):
        """Test slug removes special characters."""
        result = GroupManager.slugify("My (Test) Group!")
        assert result == "my-test-group"

    def test_multiple_spaces(self):
        """Test slug handles multiple spaces."""
        result = GroupManager.slugify("Too   Many   Spaces")
        assert result == "too-many-spaces"


class TestIPMatching:
    """Tests for IP address pattern matching."""

    def test_exact_ip_match(self):
        """Test exact IP matching."""
        assert GroupManager.ip_matches("192.168.1.100", "192.168.1.100") is True
        assert GroupManager.ip_matches("192.168.1.100", "192.168.1.101") is False

    def test_ip_range_match(self):
        """Test IP range matching."""
        assert GroupManager.ip_matches("192.168.1.100-200", "192.168.1.150") is True
        assert GroupManager.ip_matches("192.168.1.100-200", "192.168.1.100") is True
        assert GroupManager.ip_matches("192.168.1.100-200", "192.168.1.200") is True
        assert GroupManager.ip_matches("192.168.1.100-200", "192.168.1.50") is False

    def test_cidr_match(self):
        """Test CIDR notation matching."""
        assert GroupManager.ip_matches("192.168.1.0/24", "192.168.1.100") is True
        assert GroupManager.ip_matches("192.168.1.0/24", "192.168.1.1") is True
        assert GroupManager.ip_matches("192.168.1.0/24", "192.168.2.1") is False

    def test_wildcard_ip_match(self):
        """Test wildcard IP matching."""
        assert GroupManager.ip_matches("192.168.1.*", "192.168.1.100") is True
        assert GroupManager.ip_matches("192.168.*.*", "192.168.5.100") is True


class TestExportImport:
    """Tests for export/import functionality."""

    @pytest.fixture
    def group_manager(self, tmp_path):
        """Create a GroupManager with temporary storage."""
        groups_file = tmp_path / "groups.json"
        gm = GroupManager()
        gm._path = groups_file
        return gm

    def test_export_groups(self, group_manager):
        """Test exporting groups to dict."""
        group_manager.create_group("Test Group", "Description")
        group_manager.add_member("test-group", "AA:BB:CC:DD:EE:FF", "Device")

        data = group_manager.export_groups()

        assert "version" in data
        assert "groups" in data
        assert "test-group" in data["groups"]

    def test_import_groups(self, group_manager, tmp_path):
        """Test importing groups from dict."""
        data = {
            "version": 1,
            "groups": {
                "imported-group": {
                    "name": "Imported Group",
                    "type": "static",
                    "members": [
                        {"mac": "AA:BB:CC:DD:EE:FF", "alias": "Device"}
                    ],
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                }
            }
        }

        count = group_manager.import_groups(data)

        assert count == 1
        result = group_manager.get_group("imported-group")
        assert result is not None


class TestAutoGroupEvaluation:
    """Tests for auto group client evaluation."""

    @pytest.fixture
    def group_manager(self, tmp_path):
        """Create a GroupManager with temporary storage."""
        groups_file = tmp_path / "groups.json"
        gm = GroupManager()
        gm._path = groups_file
        return gm

    @pytest.fixture
    def sample_clients(self):
        """Sample clients for testing."""
        return [
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "ip": "192.168.1.100",
                "name": "iPhone",
                "hostname": "iphone",
                "oui": "Apple",
                "network": "Default",
                "is_wired": False,
            },
            {
                "mac": "11:22:33:44:55:66",
                "ip": "192.168.1.101",
                "name": "MacBook",
                "hostname": "macbook",
                "oui": "Apple",
                "network": "Default",
                "is_wired": True,
            },
            {
                "mac": "22:33:44:55:66:77",
                "ip": "192.168.100.50",
                "name": "Galaxy",
                "hostname": "galaxy",
                "oui": "Samsung",
                "network": "Guest",
                "is_wired": False,
            },
        ]

    def test_evaluate_vendor_rule(self, group_manager, sample_clients):
        """Test evaluating auto group with vendor rule."""
        rules = AutoGroupRules(vendor=["Apple"])
        group_manager.create_group("Apple Devices", group_type="auto", rules=rules)

        matches = group_manager.evaluate_auto_group("apple-devices", sample_clients)

        assert len(matches) == 2
        macs = [c["mac"] for c in matches]
        assert "AA:BB:CC:DD:EE:FF" in macs
        assert "11:22:33:44:55:66" in macs

    def test_evaluate_network_rule(self, group_manager, sample_clients):
        """Test evaluating auto group with network rule."""
        rules = AutoGroupRules(network=["Guest"])
        group_manager.create_group("Guest Devices", group_type="auto", rules=rules)

        matches = group_manager.evaluate_auto_group("guest-devices", sample_clients)

        assert len(matches) == 1
        assert matches[0]["mac"] == "22:33:44:55:66:77"

    def test_evaluate_connection_type_rule(self, group_manager, sample_clients):
        """Test evaluating auto group with connection type rule."""
        rules = AutoGroupRules(conn_type=["wireless"])
        group_manager.create_group("Wireless Devices", group_type="auto", rules=rules)

        matches = group_manager.evaluate_auto_group("wireless-devices", sample_clients)

        assert len(matches) == 2
        macs = [c["mac"] for c in matches]
        assert "AA:BB:CC:DD:EE:FF" in macs
        assert "22:33:44:55:66:77" in macs

    def test_evaluate_combined_rules_and_logic(self, group_manager, sample_clients):
        """Test that different rule types use AND logic."""
        rules = AutoGroupRules(vendor=["Apple"], conn_type=["wireless"])
        group_manager.create_group("Wireless Apple", group_type="auto", rules=rules)

        matches = group_manager.evaluate_auto_group("wireless-apple", sample_clients)

        assert len(matches) == 1
        assert matches[0]["mac"] == "AA:BB:CC:DD:EE:FF"


class TestPersistence:
    """Tests for file persistence."""

    @pytest.fixture
    def groups_file(self, tmp_path):
        """Path to temporary groups file."""
        return tmp_path / "groups.json"

    def test_data_persists_after_save(self, groups_file):
        """Test that data persists after saving."""
        gm1 = GroupManager()
        gm1._path = groups_file
        gm1.create_group("Persistent Group")

        # Create new manager instance
        gm2 = GroupManager()
        gm2._path = groups_file

        result = gm2.get_group("persistent-group")
        assert result is not None
        assert result[1].name == "Persistent Group"

    def test_handles_corrupted_file(self, groups_file):
        """Test handling of corrupted JSON file."""
        groups_file.write_text("not valid json {{{")

        gm = GroupManager()
        gm._path = groups_file

        # Should start fresh without error
        groups = gm.list_groups()
        assert len(groups) == 0
