from setuptools import find_packages, setup

install_requires = ["twilio==7.16.1"]
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()
setup(
    name="textfy",
    version="0.3",
    description="Send text message with Twilio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="JuYoung Oh",
    author_email="juyoung.oh@snu.ac.kr",
    url="https://github.com/ojy0216/textfy",
    license="MIT",
    packages=find_packages(exclude=["test"]),
    python_requires=">=3",
    install_requires=install_requires,
    keywords=["sms", "twilio"],
)
