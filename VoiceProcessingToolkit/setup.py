from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="VoiceProcessingToolkit",
    version="0.1.0",
    author="Kristoffer Vatnehol",
    author_email="kristoffer.vatnehol@appacia.com",
    description="A comprehensive library for voice processing tasks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-github/VoiceProcessingToolkit",
    project_urls={
        "Bug Tracker": "https://github.com/your-github/VoiceProcessingToolkit/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "VoiceProcessingToolkit"},
    packages=find_packages(where="VoiceProcessingToolkit"),
    python_requires=">=3.6",
    install_requires=[
        "PyAudio~=0.2.14",
        "python-dotenv~=1.0.0",
        "setuptools~=68.2.2",
        "openai~=1.3.7",
        "requests~=2.31.0",
        "elevenlabs~=0.2.27",
        "numpy~=1.26.2",
        "pvcobra~=2.0.1",
        "pvkoala~=2.0.0",
        "pvporcupine~=3.0.1",
        "pygame~=2.5.2",
    ],
)
