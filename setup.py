##### Created By rel_easy ##########################
import setuptools
from altimeter_desktop_tool.version import __version__
setuptools.setup(
    name="altimeter-desktop-tool",
    version=__version__,
    author="Joran Beasley",
    author_email="joranbeasley@gmail.com",
    url="https://pypi.org/simple/altimeter-desktop-tool/",
    description="desc",
    packages=setuptools.find_packages(),
    entry_points={
        # provided for reference
        # 'console_scripts':['myscript=altimeter_desktop_tool.cli:main'],
    },

    # uncomment for auto install requirements
    # install_requires=['click','bs4','requests','six','pySystem'],
    # uncomment for classifiers
    #classifiers=[
    #    "Programming Language :: Python :: 3",
    #    "License :: OSI Approved :: MIT License",
    #    "Operating System :: OS Independent",
    #],

    # uncomment for python version requirements
    # python_requires='>=2.7',
)
##### END ###################################
