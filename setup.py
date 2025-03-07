from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="VoiceProcessingToolkit",
    version="2.0.0",
    author="Kristoffer Vatnehol",
    author_email="kristoffer.vatnehol@appacia.com",
    description="A comprehensive library for voice processing tasks such as wake word detection, speech recognition, "
                "and transcription.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kristofferv98/VoiceProcessingToolkit.git",
    project_urls={
        "Bug Tracker": "https://github.com/kristofferv98/VoiceProcessingToolkit.git",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=find_packages(where="."),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "PyAudio~=0.2.14",
        "python-dotenv~=1.0.1",
        "requests~=2.32.3",
        "elevenlabs~=1.52.0",
        "numpy~=2.2.3",
        "pvcobra~=2.0.5",
        "pvkoala~=2.0.4",
        "pvporcupine~=3.0.5",
        "pygame~=2.6.1",
        "termcolor~=2.5.0",
    ],
    package_data={
        'VoiceProcessingToolkit': ['wake_word_detector/Wav_MP3/*.wav'],
    },
    zip_safe=False,
)
