from setuptools import setup, find_packages


setup(
    name="py_rpc",
    version="1.0.0",
    author="ZhangDong",
    author_email="785576549@qq.com",
    description="A simple and external rpc framework.",
    packages=find_packages(),
    license="MIT",
    install_requires=[
        "gevent"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
