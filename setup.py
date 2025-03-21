from setuptools import setup, find_packages

setup(
    name="finder",
    version="0.2",
    packages=find_packages(),
    install_requires=["watchdog"],
    entry_points={
        "console_scripts": [
            "finder = src.interface:run",
        ],
    },
)
