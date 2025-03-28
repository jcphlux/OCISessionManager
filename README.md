# ![OCI Session Manager Logo](./icon.png) OCI Session Manager

**OCI Session Manager** is a lightweight system tray application for Windows, macOS, and Linux that helps maintain a persistent SSH connection to your Oracle Cloud Infrastructure (OCI) Bastion server.

## ⚠️ macOS Installation Note

When launching the app for the first time on macOS, you may see a warning that the developer cannot be verified.

To open the app:

1. **Right-click** the `.app` file and choose **Open**
2. When prompted, click **Open** again

This is expected behavior with unsigned macOS apps. You only need to do this once.

---

## 💡 Features

- System tray application with red/green connection status
- Automatically reconnects on connection loss
- Stores SSH config (username, key, and bastion address)
- Cross-platform support for Windows, macOS, and Linux
- Clean native UI using Tkinter and sv-ttk

---

## 🚀 Installation

### 🪟 Windows

Download the latest `.exe` installer from the [Releases](https://github.com/jcphlux/OCISessionManager/releases) page and run it.

### 🍎 macOS

1. Download the `.dmg` file from the [Releases](https://github.com/jcphlux/OCISessionManager/releases)
2. Open the `.dmg` and drag **OCI Session Manager.app** to your Applications folder
3. **Right-click → Open** the first time to bypass the security warning

### 🐧 Linux

1. Download the `.AppImage` or `.tar.gz` file from the [Releases](https://github.com/jcphlux/OCISessionManager/releases)
2. Make it executable: `chmod +x OCI-Session-Manager.AppImage`
3. Run it: `./OCI-Session-Manager.AppImage`

---

<!-- ## 🔧 Configuration

On first launch, you'll be prompted to enter:

- **SSH Username**
- **Bastion Host** (e.g. `bastion.region.oci.oraclecloud.com`)
- **Private Key Path** (`~/.ssh/id_rsa` or a custom path)

These settings are saved locally in a configuration file for future use. -->

---

## 🛠️ Development Setup

```bash
git clone https://github.com/jcphlux/OCISessionManager.git
cd OCISessionManager

# Recommended to use a virtual environment
python -m venv beeware-venv
source beeware-venv/bin/activate
# On Windows: beeware-venv\Scripts\activate

pip install -r requirements.txt

# Use Briefcase to run the app
briefcase dev
```

---

## 📦 Packaging

This project uses [Briefcase](https://briefcase.readthedocs.io/en/latest/) for cross-platform native packaging.

### Build & Package

```bash
briefcase create
briefcase build
briefcase package --adhoc-sign
```

### Run packaged app

```bash
briefcase run
```

---

## 🧪 Testing

You can run the app locally using:

```bash
briefcase dev
```

Tests (if any in future) will go under a `tests/` directory.

---

## 📄 License

MIT License © 2025 [JCPhlux](https://github.com/jcphlux)

---

## 🙌 Credits

Built using:

- [Python](https://www.python.org/)
- [Tkinter + sv-ttk](https://github.com/rdbende/sv-ttk)
- [Briefcase](https://github.com/beeware/briefcase)
- [OCI SDK](https://github.com/oracle/oci-python-sdk)
