from icemet_sensor import __version__

from setuptools import setup, find_packages

with open("README.md") as fp:
	readme = fp.read()

with open("requirements.txt") as fp:
	requirements = fp.read().splitlines()

setup(
	name="icemet-sensor",
	version=__version__,
	packages=find_packages(),
	
	install_requires=requirements,
	
	author="Eero Molkoselkä",
	author_email="eero.molkoselka@gmail.com",
	description="Client software for ICEMET sensor",
	long_description=readme,
	url="https://github.com/molkoback/icemet-sensor",
	license="MIT",
	
	entry_points={
		"console_scripts": [
			"icemet-sensor = icemet_sensor.ui.icemet_sensor:main",
			"icemet-camera-param = icemet_sensor.ui.icemet_camera_param:main",
		]
	},
	
	classifiers=[
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 3",
		"Topic :: Internet :: File Transfer Protocol (FTP)",
		"Topic :: Scientific/Engineering :: Atmospheric Science",
		"Topic :: Software Development :: Embedded Systems"
	]
)
