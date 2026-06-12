# this will help use package as a module, meaning anyone can use it by installing it with pip install -e . in the root directory of the project
from typing import List
from setuptools import setup, find_packages


def read_requirements(file_path:str) -> List[str]:
    requirements = []
    with open(file_path) as f:
        for line in f:
            requirements.append(line.strip())
        
    if "-e ." in requirements: # this is used to add the setup.py file to the requirements.txt file, but we don't want it to be installed as a package, so we remove it from the list of requirements
        requirements.remove("-e .")
    
    return requirements




setup(
    name="mlproject",
    version="0.1",
    packages=find_packages(),
    author="Penzen",
    author_email="penzenlama@gmail.com",
    install_requires=read_requirements("requirement.txt")
)