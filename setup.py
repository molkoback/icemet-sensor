from icemet_sensor import version

from setuptools import setup, find_packages

with open("README.md") as fp:
	readme = fp.read()

with open("requirements.txt") as fp:
	requirements = fp.read().splitlines()

setup(
	name="icemet-sensor",
	version=version,
	packages=find_packages(),
	
	install_requires=requirements,
	extras_require={
		"myrio": ["psutil>=5.7.2"],
		"picolas": ["pyserial>=3.4"],
		"pylon": ["pypylon>=1.5.1"],
		"spin": ["spinnaker-python>=1.20.0.14"],
		"xyt01": ["pyserial>=3.4"]
	},
	
	package_data={"icemet_sensor": ["data/*"]},
	
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
		"Programming Language :: Python :: 3.6",
		"Topic :: Internet :: File Transfer Protocol (FTP)",
		"Topic :: Scientific/Engineering :: Atmospheric Science",
		"Topic :: Software Development :: Embedded Systems"
	]
)
