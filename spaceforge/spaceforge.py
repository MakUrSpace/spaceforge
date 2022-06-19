from subprocess import run
from dataclasses import dataclass

import boto3
import solid as sp


@dataclass
class ForgeOperation:
    operationType: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0])

    def execute(self, model):
        return model


@dataclass
class MoveObjectOperation(ForgeOperation):
    operands: []

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1:4])


@dataclass
class RotateOperation(MoveObjectOperation):
    def execute(self, model):
        return sp.rotate(self.operands)(model)


@dataclass
class TranslateOperation(MoveObjectOperation):
    def execute(self, model):
        return sp.translate(self.operands)(model)


@dataclass
class CombineOperation(ForgeOperation):
    secondAsset: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1])

    def execute(self, model):
        boto3.client("s3").download_file(
            "spaceforge",
            f"models/{self.secondAsset}",
            f"/tmp/{self.secondAsset}")
        secondAsset = sp.import_stl(f"/tmp/{self.secondAsset}")
        return model + secondAsset


@dataclass
class EngraveOperation(ForgeOperation):
    engravingTemplate: str
    scale: []

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1:4])

    def execute(self, model):
        boto3.client("s3").download_file(
            "spaceforge",
            f"engraving_templates/{self.engravingTemplate}",
            f"/tmp/{self.engravingTemplate}")
        engravingTemplate = sp.scale(self.scale)(sp.import_stl(self.engravingTemplate))
        return model - engravingTemplate


@dataclass
class ForgeOrder:
    model: str
    operations: []
    output: str


example_event = {
    "model": "mjolnir-ragnarok-endgame.stl",
    "operations": [
        ["combine", "HammeredTriviaLogo.stl"]
    ],
    "output": "HammeredTriviaTrophy.stl"
}


def lambda_handler(event, context):
    order = ForgeOrder(**event)

    # Download model from s3
    boto3.client("s3").download_file("spaceforge", f"models/{order.model}", f"/tmp/{order.model}")

    result = sp.import_stl(f"/tmp/{order.model}")
    for op in order.operations:
        if op[0] == "rotate":
            result = RotateOperation.fromGenericOperation(op).execute(result)
        elif op[0] == "translate":
            result = TranslateOperation.fromGenericOperation(op).execute(result)
        elif op[0] == "combine":
            result = CombineOperation.fromGenericOperation(op).execute(result)
        elif op[0] == "engrave":
            result = EngraveOperation.fromGenericOperation(op).execute(result)
        else:
            raise Exception(f"Unrecognized operation: {op}")

    if result is not None:
        sp.scad_render_to_file(result, f"/tmp/{order.model}.scad")
        run(["/var/task/openscad", "-o", f"/tmp/{order.model}", f"/tmp/{order.model}.scad"])
        boto3.client("s3").upload_file(f"/tmp/{order.model}", "spaceforge", f"results/{order.output}")

    return 200, f"s3://spaceforge/results/{order.output}"


if __name__ == "__main__":
    print(lambda_handler(None, None))
