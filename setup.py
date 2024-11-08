from setuptools import find_packages, setup

setup(
    name="ControlPanel",
    version="0.0.1",
    author="Dachboden",
    author_email="info@dachboden.berlin",
    packages=find_packages(exclude=[]),
    entry_points={
        "console_scripts": [
            "controlpanel = controlpanel.main:main",
            "transfer = controlpanel.micropython_sdk.transfer.transfer:transfer",
        ]
    },
    python_requires=">=3.12",
    install_requires=["pygame",
                      "pyftdi",
                      "moderngl",
                      "numpy-quaternion",
                      "numpy-stl",
                      "opencv-python",
                      ],
)
