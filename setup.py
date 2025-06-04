from setuptools import setup, find_packages

setup(
    name="facephantom-qa",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "opencv-python",
        "pydicom",
        "matplotlib",
        "pylinac"
    ],
    entry_points={
        'console_scripts': [
            'facephantom-qa = facephantom_qa.main:main'
        ]
    },
    author="Alex Hastava",
    description="Tool for QA analysis using Face Phantom and EPID-acquired DICOMs.",
    license="MIT",
)
