import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stg",
    version="0.0.1",
    author="Alexander Gabriel",
    author_email="einalex@4d6.de",
    description="A traffic generator for the Syscoin network.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/einalex/sbt",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pycrypto>=2.6.1",
        "requests"
    ],
    python_requires='>=3.6',
    scripts=[
        'scripts/stg',
    ]
)
