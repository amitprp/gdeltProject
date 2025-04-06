from setuptools import setup, find_packages

setup(
    name="jewwatch",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0,<1.0.0",
        "uvicorn[standard]>=0.15.0,<1.0.0",
        "motor>=2.5.0,<4.0.0",
        "pandas>=1.3.0,<2.0.0",
        "gdeltdoc>=1.5.0",
        "gdelt>=0.1.10.5.2",
        "python-dotenv>=0.19.0",
        "pydantic>=1.8.0,<2.0.0",
    ],
)
