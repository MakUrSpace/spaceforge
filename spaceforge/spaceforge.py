
from dataclasses import dataclass

from sf_operations import Spaceforge


@dataclass
class ForgeOrder:
    operations: []


example_event = {
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


def lambda_handler(event, context):
    order = ForgeOrder(**event)
    [Spaceforge.operate(op) for op in order.operations]
    return 200, "Spaceforge Operation Complete"


if __name__ == "__main__":
    lambda_handler(example_event, None)
