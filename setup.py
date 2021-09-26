from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in dac_qcs/__init__.py
from dac_qcs import __version__ as version

setup(
	name="dac_qcs",
	version=version,
	description="Dubai Autism Center ERPNext Module",
	author="Quark Cyber Systems FZC",
	author_email="info@quarkcs.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
