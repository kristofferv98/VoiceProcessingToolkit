from setuptools import setup, find_packages

setup(
    name='VoiceProcessingToolkit',
    version='1.0.0',
    author='Kristoffer Vatnehol',
    author_email='kristoffer.vatnehol@appacia.com',
    packages=find_packages(),
    install_requires=[
        'pvcobra~=2.0.1',
        'pyaudio~=0.2.14',
        'pvporcupine~=3.0.1',
        'pygame~=2.5.2',
        'python-dotenv~=1.0.0',
        'setuptools~=68.2.0',
        'openai~=1.3.7',
        'requests~=2.31.0',
        'numpy~=1.26.2',
        'pvkoala~=2.0.0',
    ],
    license='MIT',
    description='A comprehensive toolkit for voice detection, wake word detection, text-to-speech, and audio '
                'processing.',
    long_description_content_type='text/markdown',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    url='https://github.com/yourorganization/voiceprocessingtoolkit',  # Ensure this URL points to the actual
    # repository.
    keywords='voice-processing text-to-speech wake-word-detection audio-processing',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
