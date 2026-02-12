"""
Wellness Studio - Setup Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="wellness-studio",
    version="1.0.0",
    author="Wellness Studio",
    description="Transform medical data into natural wellness plans using HuggingFace models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wellness-studio/wellness-studio",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "audio": ["openai-whisper>=20231117", "librosa>=0.10.1", "soundfile>=0.12.1"],
        "gpu": ["bitsandbytes>=0.41.0"],
        "dev": ["pytest>=7.4.0", "black>=23.0.0", "isort>=5.12.0"],
    },
    entry_points={
        "console_scripts": [
            "wellness-studio=wellness_studio.cli:main",
        ],
    },
)
