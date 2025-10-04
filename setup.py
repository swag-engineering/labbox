from setuptools import setup, find_packages
import os

with open(os.path.join("labbox", "version.py"), "r") as f:
	for line in f:
		if line.startswith("__version__"):
			version = line.split("=")[-1].strip().strip('"')
			break
print(version)

reqs = []
with open('requirements.txt') as fp:
    reqs.append(fp.read())

setup(
	name = "LabBox",
	version="0.1",
	author = "SWAG Engineering",
	license = "MIT",
	description = ("LabBox is a PyQt-based tool that is mainly used "
		"to play&learn and monitor any activity related to a microcontroller"),
	keywords = "MCU PyQt microcontroller embedded tutorial",
	url = "https://gitlab.com/swag_engineering/labbox",
	packages = find_packages(),
	long_description = open("README.md", "rb").read().decode("utf-8"),
	long_description_content_type='text/markdown',
	include_package_data=True,
	classifiers = [
		"Development Status :: 4 - Beta",
		"Environment :: X11 Applications :: Qt",
		"Environment :: MacOS X",
		"Intended Audience :: Developers",
		"Intended Audience :: Education",
		"Natural Language :: English",
		"Programming Language :: Python :: 3 :: Only",
		"Topic :: Scientific/Engineering"
	],
	scripts = ["scripts/labbox", "scripts/labbox_generator"],
	install_requires = reqs
)