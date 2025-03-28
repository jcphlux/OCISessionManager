import ensurepip
import importlib
import importlib.util
import subprocess
import sys

REQUIRED_PACKAGES = [
    "pip-tools",
    "tomlkit",
    "packaging",
]


def ensure_dependencies_installed():
    print("📦 Checking for required dev tools...")

    for pkg in ["pip-tools", "tomlkit", "packaging"]:
        module = pkg.replace("-", "_")
        if importlib.util.find_spec(module) is None:
            print(f"🔍 Missing: {pkg} - Installing into active environment...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg], check=True
                )
            except FileNotFoundError:
                print("⚠️ pip not found, attempting to bootstrap with ensurepip...")
                ensurepip.bootstrap()
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg], check=True
                )
        else:
            print(f"✅ {pkg} is already installed")


def run_pip_compile():
    print("🔄 Running pip-compile...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "piptools",
            "compile",
            "--strip-extras",
            "--no-emit-find-links",
            "-o",
            "requirements.txt",
            "requirements.in",
        ],
        check=True,
    )

    print("✅ requirements.txt updated")


def parse_requirements_in(filename):
    from packaging.requirements import Requirement

    base = []
    windows = []
    mac = []
    linux = []

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            req = Requirement(line)
            marker = req.marker

            if marker is None:
                base.append(str(req))
                continue

            marker_str = str(marker).lower()
            added = False

            if "win" in marker_str:
                windows.append(str(req))
                added = True
            if "mac" in marker_str or "darwin" in marker_str:
                mac.append(str(req))
                added = True
            if "linux" in marker_str:
                linux.append(str(req))
                added = True

            if not added:
                base.append(str(req))  # fallback

    return {"base": base, "windows": windows, "mac": mac, "linux": linux}


def update_pyproject(deps_by_platform):
    """Update pyproject.toml with the dependencies from requirements.in."""
    import tomlkit
    from packaging.requirements import Requirement

    def clean_reqs(req_list):
        """Strip environment markers from a list of requirements."""
        cleaned = []
        for req in req_list:
            parsed = Requirement(req)
            parsed.marker = None  # remove marker
            cleaned.append(str(parsed))
        return cleaned

    def make_multiline_array(items):
        """Create a tomlkit array that formats over multiple lines."""
        array = tomlkit.array()
        for item in items:
            array.append(item)
        array.multiline(True)
        return array

    with open("pyproject.toml", "r", encoding="utf-8") as f:
        pyproject = tomlkit.parse(f.read())

    app = pyproject["tool"]["briefcase"]["app"]["ocisessionmanager"]

    # Base
    app["requires"] = make_multiline_array(clean_reqs(deps_by_platform["base"]))

    # Platform-specific
    for platform in ["windows", "mac", "linux"]:
        section = app.get(platform, tomlkit.table())
        section["requires"] = make_multiline_array(
            clean_reqs(deps_by_platform.get(platform, []))
        )
        app[platform] = section

    with open("pyproject.toml", "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(pyproject))

    print("✅ pyproject.toml updated from requirements.in")


if __name__ == "__main__":
    ensure_dependencies_installed()
    run_pip_compile()
    deps = parse_requirements_in("requirements.in")
    update_pyproject(deps)
