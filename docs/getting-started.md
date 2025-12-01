# Getting Started

Get up and running with UI-CLI in under 5 minutes.

## Quick Install

```bash
# Clone the repository
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli

# Install (choose one)
pip install -e .                    # Using pip
# OR
conda env create -f environment.yml  # Using conda
conda activate ui-cli
pip install -e .
```

## Configure

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

=== "Cloud API"

    ```bash
    # Get your API key from: https://unifi.ui.com → Settings → API
    UNIFI_API_KEY=your-api-key-here
    ```

=== "Local Controller"

    ```bash
    UNIFI_CONTROLLER_URL=https://192.168.1.1
    UNIFI_CONTROLLER_USERNAME=admin
    UNIFI_CONTROLLER_PASSWORD=yourpassword
    UNIFI_CONTROLLER_SITE=default
    UNIFI_CONTROLLER_VERIFY_SSL=false
    ```

=== "Both"

    ```bash
    # Cloud API
    UNIFI_API_KEY=your-api-key-here

    # Local Controller
    UNIFI_CONTROLLER_URL=https://192.168.1.1
    UNIFI_CONTROLLER_USERNAME=admin
    UNIFI_CONTROLLER_PASSWORD=yourpassword
    UNIFI_CONTROLLER_SITE=default
    UNIFI_CONTROLLER_VERIFY_SSL=false
    ```

## Verify Installation

```bash
# Check Cloud API connection
./ui status

# Check Local Controller connection
./ui lo health
```

## Your First Commands

### Cloud API

```bash
# List all your controllers
./ui hosts list

# List all devices across all sites
./ui devices list

# Check ISP performance
./ui isp metrics
```

### Local Controller

```bash
# List connected clients
./ui lo clients list

# Get detailed client status
./ui lo clients status my-iPhone

# List network devices
./ui lo devices list
```

## Output Formats

All commands support multiple output formats:

```bash
./ui devices list              # Table (default)
./ui devices list -o json      # JSON (for scripting)
./ui devices list -o csv       # CSV (for spreadsheets)
```

## Next Steps

- [Installation](installation.md) - Detailed installation options
- [Configuration](configuration.md) - All configuration options
- [Commands](commands/index.md) - Full command reference
- [Examples](examples.md) - Real-world usage examples
