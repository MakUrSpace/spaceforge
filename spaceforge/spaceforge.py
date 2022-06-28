import json
from dataclasses import dataclass
from subprocess import run

import boto3
import solid as sp
from stl import mesh


memory = {}
openscad_path = "/var/task/openscad"
bucket = "makurspace-static-assets"
assets_path_prefix = "spaceforge_assets/"
orders_path_prefix = "spaceforge_orders/"


def bound_box(stl_path):
    model = mesh.Mesh.from_file(stl_path)
    max_x = None
    min_x = None
    max_y = None
    min_y = None
    max_z = None
    min_z = None

    for triangle in model.points:
        triangle_points = [triangle[i * 3: i * 3 + 3] for i in range(3)]
        for point in triangle_points:
            if max_x is None or point[0] > max_x:
                max_x = point[0]
            if min_x is None or point[0] < min_x:
                min_x = point[0]

            if max_y is None or point[1] > max_y:
                max_y = point[1]
            if min_y is None or point[1] < min_y:
                min_y = point[1]

            if max_z is None or point[2] > max_z:
                max_z = point[2]
            if min_z is None or point[2] < min_z:
                min_z = point[2]
    return [[max_x, min_x], [max_y, min_y], [max_z, min_z]]


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

    @classmethod
    def executeOrder(cls, order):
        global memory
        memory = {}
        [Spaceforge.operate(op) for op in order.operations]


@dataclass
class MemoryOperation(Spaceforge):
    outputMemory: str


@dataclass
class TextOperation(MemoryOperation):
    text: str
    size: float
    thickness: str
    font: str

    @classmethod
    def fromGenericOperation(cls, op):
        if len(op) == 6:
            font = op[4]
            outputMemory = op[5]
        else:
            outputMemory = op[4]
            font = "Calibri"
        return cls(op[0], outputMemory, op[1], op[2], op[3], font)

    def execute(self):
        memory[self.outputMemory] = sp.linear_extrude(self.thickness)(sp.text(self.text, self.size, font=self.font))


@dataclass
class ImportOperation(Spaceforge):
    model: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1])

    def execute(self):
        boto3.client("s3").download_file(
            bucket,
            f"{assets_path_prefix}{self.model}",
            f"/tmp/{self.model}")
        memory[self.model] = sp.import_stl(f"/tmp/{self.model}")


@dataclass
class CompileOperation(Spaceforge):
    sourceMemory: str
    outputName: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1], op[2])

    def execute(self):
        sp.scad_render_to_file(memory[self.sourceMemory], f"/tmp/{self.outputName}.scad")
        run([openscad_path, "-o", f"/tmp/{self.outputName}.stl", f"/tmp/{self.outputName}.scad"])


@dataclass
class ExportOperation(Spaceforge):
    sourceMemory: str
    outputName: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[1], op[2])

    def execute(self):
        Spaceforge.operate(["compile", self.sourceMemory, self.outputName])
        boto3.client("s3").upload_file(
            f"/tmp/{self.outputName}.stl",
            bucket,
            f"{assets_path_prefix}{self.outputName}",
            ExtraArgs={'ACL': 'public-read'})


@dataclass
class AlignOperation(MemoryOperation):
    """ ["align", "{sourceMemory}", "{targetMemory}", "{axes}", "{outputMemory}"] """
    sourceMemory: str
    targetMemory: str
    axes: []

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[4], op[1], op[2], op[3])

    def execute(self):
        Spaceforge.operate(["compile", self.sourceMemory, f"compiled_{self.sourceMemory}"])
        Spaceforge.operate(["compile", self.targetMemory, f"compiled_{self.targetMemory}"])

        sourceBB = bound_box(f"/tmp/compiled_{self.sourceMemory}.stl")
        sourceCenter = [(maxD - minD) / 2 + minD for maxD, minD in sourceBB]
        targetBB = bound_box(f"/tmp/compiled_{self.targetMemory}.stl")
        targetCenter = [(maxD - minD) / 2 + minD for maxD, minD in targetBB]

        axes = ['x', 'y', 'z']
        translation = [target - source if axis in self.axes else 0
                       for target, source, axis in zip(targetCenter, sourceCenter, axes)]
        Spaceforge.operate(["translate", self.sourceMemory, translation, self.outputMemory])


@dataclass
class TransformOperation(MemoryOperation):
    sourceMemory: str
    operands: []

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[3], op[1], op[2])


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
class CombineOperation(MemoryOperation):
    firstMemory: str
    secondMemory: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[3], op[1], op[2])

    def execute(self):
        memory[self.outputMemory] = memory[self.firstMemory] + memory[self.secondMemory]


@dataclass
class EngraveOperation(MemoryOperation):
    firstMemory: str
    secondMemory: str

    @classmethod
    def fromGenericOperation(cls, op):
        return cls(op[0], op[3], op[1], op[2])

    def execute(self):
        memory[self.outputMemory] = memory[self.firstMemory] - memory[self.secondMemory]


Spaceforge.OperationTypes = {
    "import": ImportOperation,
    "compile": CompileOperation,
    "export": ExportOperation,
    "translate": TranslateOperation,
    "rotate": RotateOperation,
    "scale": ScaleOperation,
    "text": TextOperation,
    "combine": CombineOperation,
    "engrave": EngraveOperation,
    "align": AlignOperation
}


##############################################################################################################


@dataclass
class ForgeOrder:
    orderId: str
    operations: []


example_event = {
    "orderId": "fooBar",
    "operations": [
        ["import", "hammer2.stl"],
        ["import", "HammeredTriviaLogo.stl"],
        ["rotate", "HammeredTriviaLogo.stl", [0, 0, 90.00001], "logo90"],
        ["rotate", "HammeredTriviaLogo.stl", [0, 0, 270.00001], "logo270"],
        ["translate", "logo270", [200, 0, 0], "logo270"],
        ["combine", "logo90", "logo270", "sideLogos"],
        ["text", "Hammered", 16, 4, "hammered"],
        ["rotate", "hammered", [90, 0, 0], "hammered"],
        ["translate", "hammered", [-54, 2, 74.5], "hammered"],
        ["text", "Trivia", 16, 4, "trivia"],
        ["rotate", "trivia", [90, 0, 0], "trivia"],
        ["translate", "trivia", [-25, 2, 54.5], "trivia"],
        ["combine", "hammered", "trivia", "hammeredTrivia"],
        ["text", "1st Place", 12, 4, "firstPlace"],
        ["rotate", "firstPlace", [90, 0, 0], "firstPlace"],
        ["translate", "firstPlace", [-34, 2, 40], "firstPlace"],
        ["combine", "hammeredTrivia", "firstPlace", "frontNamePlate"],
        ["text", "Ruckus Pizza", 16, 4, "pizza"],
        ["rotate", "pizza", [90, 0, 0], "pizza"],
        ["translate", "pizza", [-68, 2, 60.5], "pizza"],
        ["text", "6-19-2022", 12, 4, "date"],
        ["rotate", "date", [90, 0, 0], "date"],
        ["translate", "date", [-37.5, 2, 45], "date"],
        ["combine", "pizza", "date", "backNamePlate"],
        ["scale", "hammer2.stl", [4, 4, 4], "trophy"],
        ["translate", "trophy", [-66, -31, 0], "trophy"],
        ["engrave", "trophy", "sideLogos", "trophy"],
        ["translate", "trophy", [0, 60, 0], "trophy"],
        ["engrave", "trophy", "frontNamePlate", "trophy"],
        ["rotate", "trophy", [0, 0, 180], "trophy"],
        ["translate", "trophy", [0, 120, 0], "trophy"],
        ["engrave", "trophy", "backNamePlate", "trophy"],
        ["export", "trophy", "HammeredTriviaTrophy.stl"]
    ]
}


example_order = ForgeOrder(**example_event)


def lambda_handler(event, context):
    print(f"Spaceforge received {event}")
    order = ForgeOrder(**event)
    with open("/tmp/order.json", "w") as f:
        f.write(json.dumps(event, indent=2))
    boto3.client("s3").upload_file(f"/tmp/order.json", bucket, f"{orders_path_prefix}order-{order.orderId}.json", ExtraArgs={'ACL': 'public-read'})
    Spaceforge.executeOrder(order)
    return 200, f"Spaceforge Operation {order.orderId} Complete"


if __name__ == "__main__":
    lambda_handler(example_event, None)
