from setuptools import setup
from os import path
from codecs import open
from pathlib import Path

with open(path.join(Path("."), "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name="enforce",
    version="0.3.5",
    description="Python 3.5+ library for integration testing and "
    "data validation through configurable and optional runtime type hint enforcement.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/RussBaz/enforce",
    author="RussBaz",
    author_email="RussBaz@users.noreply.github.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
    ],
    keywords="typechecker validation testing runtime type-hints typing decorators",
    packages=["enforce"],
    install_requires=["wrapt"],
)
