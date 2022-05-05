from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in transafrica_payroll/__init__.py
from transafrica_payroll import __version__ as version

setup(
	name="transafrica_payroll",
	version=version,
	description="This application consist of NSSF Report, NHIF Report, HELB Report,P9A Tax Deduction Card Report, Sales Tax Report and Purchase Tax Report.",
	author="Christopher Njogu",
	author_email="chris@pointershub.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
