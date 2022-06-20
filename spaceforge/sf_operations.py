from subprocess import run
from dataclasses import dataclass
import solid as sp
import boto3


memory = {}


@dataclass
class Spaceforge:
    operationType: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0])

    @classmethod
    def operate(cls, op):
        if op[0] not in Spaceforge.OperationTypes:
            raise Exception(f"Unrecognized operation: {op}")

        cls.OperationTypes[op[0]].fromGenericOperation(op).execute()


@dataclass
class TextOperation(Spaceforge):
    text: str
    size: float
    thickness: str
    outputMemory: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1], op[2], op[3], op[4])

    def execute(self):
        memory[self.outputMemory] = sp.linear_extrude(self.thickness)(sp.text(self.text, self.size))


@dataclass
class ImportOperation(Spaceforge):
    model: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1])

    def execute(self):
        boto3.client("s3").download_file(
            "spaceforge",
            f"assets/{self.model}",
            f"/tmp/{self.model}")
        memory[self.model] = sp.import_stl(f"/tmp/{self.model}")


@dataclass
class ExportOperation(Spaceforge):
    sourceMemory: str
    outputModel: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1], op[2])

    def execute(self):
        sp.scad_render_to_file(memory[self.sourceMemory], f"/tmp/{self.outputModel}.scad")
        run(["openscad", "-o", f"/tmp/{self.outputModel}", f"/tmp/{self.outputModel}.scad"])
        boto3.client("s3").upload_file(f"/tmp/{self.outputModel}", "spaceforge", f"assets/{self.outputModel}")


@dataclass
class TransformOperation(Spaceforge):
    sourceMemory: str
    operands: []
    outputMemory: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1], op[2], op[3])


@dataclass
class RotateOperation(TransformOperation):
    def execute(self):
        memory[self.outputMemory] = sp.rotate(self.operands)(memory[self.sourceMemory])


@dataclass
class TranslateOperation(TransformOperation):
    def execute(self):
        memory[self.outputMemory] = sp.translate(self.operands)(memory[self.sourceMemory])


@dataclass
class ScaleOperation(TransformOperation):
    def execute(self):
        memory[self.outputMemory] = sp.scale(self.operands)(memory[self.sourceMemory])


@dataclass
class CombineOperation(Spaceforge):
    firstMemory: str
    secondMemory: str
    outputMemory: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1], op[2], op[3])

    def execute(self):
        memory[self.outputMemory] = memory[self.firstMemory] + memory[self.secondMemory]


@dataclass
class EngraveOperation(Spaceforge):
    firstMemory: str
    secondMemory: str
    outputMemory: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1], op[2], op[3])

    def execute(self):
        memory[self.outputMemory] = memory[self.firstMemory] - memory[self.secondMemory]


Spaceforge.OperationTypes = {
    "import": ImportOperation,
    "export": ExportOperation,
    "translate": TranslateOperation,
    "rotate": RotateOperation,
    "scale": ScaleOperation,
    "text": TextOperation,
    "combine": CombineOperation,
    "engrave": EngraveOperation
}
