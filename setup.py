from setuptools import setup, find_packages

setup(
    name="zakkistore-sdk",
    version="1.0.5",
    description="Official Python SDK Client Library for Zakki Store B2B API",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="ZakkiXD",
    author_email="b2b_partner@example.com",
    url="https://github.com/MrLow12/zakkistore-sdk",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
