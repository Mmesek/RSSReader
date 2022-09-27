import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    _requirements = [i.strip() for i in f.readlines()]

requirements = []
for req in _requirements:
    if "://" in req:
        name = req.split('/')[-1].split(".")[0]
        req = f"{name} @ {req}"
    requirements.append(req)

setuptools.setup(
    name="mRSS",
    version="1.0.0",
    author="Mmesek",
    description="RSS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mmesek/RSSReader",
    project_urls={
        "Bug Tracker": "https://github.com/Mmesek/RSSReader/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.9",
)