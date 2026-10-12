"""Build a Python 3.12 / Linux x86_64 Lambda ZIP using locked uv dependencies."""

import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


def main() -> None:
    """Bundle only application code, fictional fixtures, and dependencies."""
    root = Path(__file__).resolve().parent.parent
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("Install uv and make it available on PATH before building.")
    destination = root / "dist" / "powerdesk-lambda.zip"

    # 1. Build in a fresh temporary directory; never copy the local virtualenv.
    with TemporaryDirectory(prefix="powerdesk-lambda-") as directory:
        staging = Path(directory)
        requirements = staging / "requirements.txt"
        package = staging / "package"
        subprocess.run(
            [uv, "export", "--locked", "--no-dev", "--no-emit-project",
             "--format", "requirements.txt", "--output-file", str(requirements)],
            cwd=root, check=True, stdout=subprocess.DEVNULL,
        )

        # 2. Include the locked SDK and Linux wheels, even when building on macOS.
        subprocess.run(
            [uv, "pip", "install", "--requirements", str(requirements),
             "--require-hashes", "--only-binary", ":all:",
             "--python-version", "3.12", "--python-platform", "x86_64-manylinux2014",
             "--target", str(package)],
            cwd=root, check=True,
        )

        # 3. Copy our package and only the two fictional input JSON files.
        shutil.copytree(
            root / "src" / "power_desk_brief", package / "power_desk_brief",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        fixtures = package / "data" / "synthetic"
        fixtures.mkdir(parents=True)
        for name in ("emails.json", "news.json"):
            shutil.copy2(root / "data" / "synthetic" / name, fixtures / name)

        # 4. Put importable packages at the ZIP root with readable permissions.
        archive = staging / "powerdesk-lambda.zip"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as file:
            for path in sorted(package.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    path.chmod(0o644)
                    file.write(path, path.relative_to(package))
        destination.parent.mkdir(exist_ok=True)
        shutil.copy2(archive, destination)

    print(f"Built: {destination}")
    print(f"ZIP size: {destination.stat().st_size / 1024 / 1024:.1f} MiB")
    print("Runtime: Python 3.12; architecture: x86_64")
    print("Handler: power_desk_brief.lambda_handler.handler")
    print("No AWS resources were created and no model was called.")


if __name__ == "__main__":
    main()
