from setuptools import find_packages, setup


setup(
    name='summer',
    packages=find_packages(include=['summer*']),
    version='0.1.0',
    description='Summer dependency injection and scheduling framework',
    author='Benedikt Engeser',
    license='MIT',
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)