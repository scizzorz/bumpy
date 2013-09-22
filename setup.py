from setuptools import setup

setup(
	name='bumpy',
	version='0.2.3',
	description='Create build files and CLI tools easily.',
	long_description=open('README.rst').read(),
	url='http://github.com/scizzorz/bumpy',
	license='MIT',
	author='John Weachock',
	author_email='jweachock@gmail.com',
	py_modules=['bumpy'],
	include_package_data=True,
	scripts=['bin/bumpy'],
)
