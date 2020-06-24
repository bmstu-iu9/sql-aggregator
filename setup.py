from setuptools import setup, find_packages


setup(
    name='multidb',
    version='0.1',
    package_data={
        '': [
            'logging.yaml'
        ]
    },
    packages=find_packages(),
    install_requires=[
        'pyodbc>=4.0.30',
        'PyPika>=0.37.7',
        'pyqt5==5.13.0',
        'PyYAML'
    ],
    url='',
    license='',
    author='Chugunov Denis',
    author_email='',
    description='Aggregator DBMS'
)
