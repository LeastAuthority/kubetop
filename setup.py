# Copyright Least Authority Enterprises.
# See LICENSE for details.

from setuptools import find_packages, setup

_metadata = {}
with open("src/kubetop/_metadata.py") as f:
    exec(f.read(), _metadata)

setup(
    name="kubetop",
    version=_metadata["version_string"],
    description="A top(1)-like tool for Kubernetes.",
    author="kubetop Developers",
    url="https://github.com/leastauthority/kubetop",
    license="MIT",
    zip_safe=False,
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "bitmath",
        "attrs",
        "pyyaml",
        "twisted[tls]!=17.1.0",
        "treq",
        "txkube",
    ],
    extras_require={
        "dev": [
            "hypothesis",
        ],
    },
    entry_points={
        "console_scripts": [
            "kubetop = kubetop._script:main",
        ],
    },
)
