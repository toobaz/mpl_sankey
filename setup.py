import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mpl_sankey",
    version="0.1.0",
    author="Pietro Battiston",
    author_email="me@pietrobattiston.it",
    description="Sankey plots with Matplotlib",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/toobaz/mpl_sankey",
    packages=setuptools.find_packages(),
    license='GPLv3',
    classifiers=(
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ),
)
