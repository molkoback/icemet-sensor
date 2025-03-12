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
	
	package_data={"icemet_sensor": ["data/*", "plugins/*"]},
	
	author="Eero Molkoselkä",
	author_email="eero.molkoselka@gmail.com",
	description="Client software for ICEMET sensor",
	long_description=readme,
	url="https://github.com/molkoback/icemet-sensor",
	license="MIT",
	
	entry_points={
		"console_scripts": [
			"icemet-sensor = icemet_sensor.ui.icemet_sensor:main",
			"icemet-camera-param = icemet_sensor.ui.camera_param:main",
			"icemet-laser-on = icemet_sensor.ui.laser:laser_on_main",
			"icemet-laser-off = icemet_sensor.ui.laser:laser_off_main",
			"icemet-temp-relay = icemet_sensor.ui.temp_relay:main"
		]
	},
	
	classifiers=[
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Programming Language :: Python :: 3",
		"Topic :: Scientific/Engineering :: Atmospheric Science",
		"Topic :: Software Development :: Embedded Systems"
	]
)
