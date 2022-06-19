import subprocess
from fire import Fire


def extract_openscad(image_uri):
    subprocess.call(f"docker cp {image_uri}:/root/openscad/openscad ./openscad", shell=True)


def extract_boost_lib(image_uri):
    subprocess.call(f"docker cp {image_uri}:/usr/local/lib/ ./local_lib", shell=True)


def extract_qt_libs(image_uri):
    subprocess.call(f"docker cp {image_uri}:/root/qt5-build/qtbase/lib/ ./local_qt_lib", shell=True)


def extract_everything(image_uri: str):
    print("Extracting openscad...")
    extract_openscad(image_uri)
    print("Extracting boost_lib...")
    extract_boost_lib(image_uri)
    print("Extracting qt libs...")
    extract_qt_libs(image_uri)
    print("Complete!")


if __name__ == '__main__':
    Fire(extract_everything)
