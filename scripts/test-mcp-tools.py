#!/usr/bin/env python
"""Test script to validate all MCP tools work correctly.

Run with: python scripts/test-mcp-tools.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ui_mcp.server import (
    network_status,
    network_health,
    internet_speed,
    isp_performance,
    client_count,
    device_list,
    network_list,
    find_client,
    find_device,
    client_status,
    # Action tools - skip these in automated test
    # block_client,
    # unblock_client,
    # kick_client,
    # restart_device,
    # create_voucher,
    # run_speedtest,  # Takes too long
)


def print_result(name: str, result: str, max_lines: int = 10):
    """Print test result with truncation."""
    print(f"\n{'='*60}")
    print(f"🔧 {name}")
    print('='*60)

    try:
        data = json.loads(result)
        if "error" in data:
            print(f"❌ ERROR: {data.get('message', 'Unknown error')}")
            return False

        # Print summary if available
        if "summary" in data:
            print(f"✅ {data['summary']}")
        else:
            print("✅ Success")

        # Print truncated JSON
        lines = json.dumps(data, indent=2).split('\n')
        if len(lines) > max_lines:
            for line in lines[:max_lines]:
                print(f"   {line}")
            print(f"   ... ({len(lines) - max_lines} more lines)")
        else:
            for line in lines:
                print(f"   {line}")
        return True
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON: {result[:200]}")
        return False


async def test_read_only_tools():
    """Test all read-only tools."""
    results = {}

    # Status & Health
    print("\n" + "="*60)
    print("📊 TESTING STATUS & HEALTH TOOLS")
    print("="*60)

    results["network_status"] = print_result(
        "network_status()",
        await network_status()
    )

    results["network_health"] = print_result(
        "network_health()",
        await network_health()
    )

    results["internet_speed"] = print_result(
        "internet_speed()",
        await internet_speed()
    )

    results["isp_performance"] = print_result(
        "isp_performance(hours=24)",
        await isp_performance(hours=24)
    )

    # Counts & Lists
    print("\n" + "="*60)
    print("📋 TESTING COUNT & LIST TOOLS")
    print("="*60)

    results["client_count"] = print_result(
        "client_count(by='type')",
        await client_count(by="type")
    )

    results["client_count_network"] = print_result(
        "client_count(by='network')",
        await client_count(by="network")
    )

    results["device_list"] = print_result(
        "device_list()",
        await device_list()
    )

    results["network_list"] = print_result(
        "network_list()",
        await network_list()
    )

    # Lookups - need real device/client names
    print("\n" + "="*60)
    print("🔍 TESTING LOOKUP TOOLS")
    print("="*60)

    # Get a real device name from device_list
    device_result_str = await device_list()
    device_result = json.loads(device_result_str)
    device_data = device_result.get("data", device_result) if isinstance(device_result, dict) else device_result

    if isinstance(device_data, list) and len(device_data) > 0:
        device_name = device_data[0].get("name", "")
        if device_name:
            results["find_device"] = print_result(
                f"find_device(name='{device_name}')",
                await find_device(name=device_name)
            )

    # Test find_client and client_status with a known-bad name
    # This tests that the tools handle errors gracefully
    # We expect errors here - that's correct behavior
    print("\n[Testing error handling with non-existent client]")

    result = await find_client(name="nonexistent-device-12345")
    data = json.loads(result)
    if "error" in data and "not found" in data.get("message", "").lower():
        print("✅ find_client correctly returns error for non-existent client")
        results["find_client_error_handling"] = True
    else:
        print(f"❌ Unexpected response: {result[:200]}")
        results["find_client_error_handling"] = False

    result = await client_status(name="nonexistent-device-12345")
    data = json.loads(result)
    if "error" in data and "not found" in data.get("message", "").lower():
        print("✅ client_status correctly returns error for non-existent client")
        results["client_status_error_handling"] = True
    else:
        print(f"❌ Unexpected response: {result[:200]}")
        results["client_status_error_handling"] = False

    return results


async def main():
    print("🚀 MCP Tools Test Suite")
    print("Testing all read-only tools...")
    print("(Action tools like block/restart are skipped for safety)")

    results = await test_read_only_tools()

    # Summary
    print("\n" + "="*60)
    print("📈 TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    print(f"\n  Total: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
