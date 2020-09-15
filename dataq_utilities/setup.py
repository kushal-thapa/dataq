import setuptools

def readme():
    with open("README.md", "r") as f:
        return f.read()

setuptools.setup(
    name="dataq",
    version="0.1",
    description="Utilities for interacting with DataQ devices",
    long_description=readme(),
    long_description_content_type="text/markdown",
    keywords='DataQ DI-1100',
    url="https://github.com/stanmcclellan/DataQ",
    author="Stan McClellan",
    author_email="s.mcclellan@ieee.org",
    license='GPLv3',
    packages=DataQ.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
    ],
    install_requires=['markdown'],
    python_requires='>=3.6',
)
