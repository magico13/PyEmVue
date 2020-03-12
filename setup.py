import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyemvue",
    version="0.9.3",
    author="magico13",
    description="Library for interacting with the Emporia Vue energy monitor.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/magico13/PyEmVue",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Home Automation",

    ],
    python_requires='>=2.7',
    install_requires=['warrant', 'requests'],
)