from setuptools import setup, find_packages

setup(
    name="video-analysis-app-backend",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi==0.68.0",
        "uvicorn==0.15.0",
        "python-multipart==0.0.5",
        "python-dotenv==0.19.0",
        "requests==2.26.0",
        "fpdf==1.7.2",
        "markdown==3.3.4",
        "ffmpeg-python==0.2.0",
    ],
    entry_points={
        "console_scripts": [
            "video-analysis-app-backend=main:main",
        ],
    },
)
