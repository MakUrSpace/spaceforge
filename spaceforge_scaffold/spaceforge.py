import os
from subprocess import run


def lambda_handler(event, context):
    print(f"{os.listdir('/lib/')}")
    print(f"{os.listdir('/usr/lib/')}")
    print(f"{os.listdir()}")
    print(run(["./openscad", "-o", "/tmp/VatDrain.stl", "VatDrain.scad"]))
    return 200, f"{os.listdir()}"


if __name__ == "__main__":
    print(lambda_handler(None, None))

