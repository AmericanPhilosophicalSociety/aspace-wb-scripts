"""
Setup script for backward compatibility
"""

from setuptools import setup, find_packages

setup(
    name="aspace-wb-scripts",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
)
