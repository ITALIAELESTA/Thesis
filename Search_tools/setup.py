from setuptools import setup, find_packages

setup(
    name="analysis_lib",
    version="0.1",
    packages=find_packages(),
    # This line ensures your .json file is included in the install
    package_data={'analysis_lib': ['*.json']},
    include_package_data=True,
    install_requires=[
        'pandas', 'networkx', 'numpy','matplotlib',
        # List any external libraries you use, e.g.,
        # 'pandas', 'networkx', 'numpy'
    ],
)