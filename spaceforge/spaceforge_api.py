import boto3
import botocore
import json
from uuid import uuid4
from datetime import datetime
from urllib.parse import parse_qs, unquote


def import_html_template(template_name):
    with open(f"html_templates/{template_name}") as f:
        template = f.read()
    return template


def fireSpaceforge(event):
    return 202, "Spaceforge Firing"


def serveAssetViewer(event):
    viewerTemplate = import_html_template("aframeScene.html")

    pathParameters = event.get('pathParameters', {})
    if pathParameters is not None:
        asset_name = pathParameters.get('asset_name', "Buddha.stl")
    else:
        asset_name = "Buddha.stl"

    for pattern, value in {
            "{asset_name}": asset_name,
            "{model_position}": '0, 0, 0'}.items():
        viewerTemplate = viewerTemplate.replace(pattern, value)

    return {
        "statusCode": 200,
        "headers": {"content-type": "text/html"},
        "body": viewerTemplate
    }


def serveSpaceforge(event):
    if event['httpMethod'] == 'POST':
        newOrder = json.loads(parse_qs(event['body'])['instructionEditor'][0])
        newOrder['orderId'] = str(uuid4())
        newOrder = json.dumps(newOrder)
        print(f"Creating new Spaceforge Order: {newOrder}")
        boto3.client("lambda").invoke(
            FunctionName="spaceforge-prod-sf",
            InvocationType="Event",
            Payload=newOrder)

    spaceforgeTemplate = import_html_template("spaceforge.html")
    return {
        "statusCode": 200,
        "headers": {"content-type": "text/html"},
        "body": spaceforgeTemplate
    }


hammerTrophyOrderTemplate = """{
    "orderId": "{order_id}",
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
        ["text", "{place} Place", 12, 4, "firstPlace"],
        ["rotate", "firstPlace", [90, 0, 0], "firstPlace"],
        ["translate", "firstPlace", [-34, 2, 40], "firstPlace"],
        ["combine", "hammeredTrivia", "firstPlace", "frontNamePlate"],
        ["text", "{event_venue}", 16, 4, "venue"],
        ["rotate", "venue", [90, 0, 0], "venue"],
        ["translate", "venue", [-68, 2, 60.5], "venue"],
        ["text", "{event_date}", 12, 4, "date"],
        ["rotate", "date", [90, 0, 0], "date"],
        ["translate", "date", [-37.5, 2, 45], "date"],
        ["combine", "venue", "date", "backNamePlate"],
        ["scale", "hammer2.stl", [4, 4, 4], "trophy"],
        ["translate", "trophy", [-66, -31, 0], "trophy"],
        ["engrave", "trophy", "sideLogos", "trophy"],
        ["translate", "trophy", [0, 60, 0], "trophy"],
        ["engrave", "trophy", "frontNamePlate", "trophy"],
        ["rotate", "trophy", [0, 0, 180], "trophy"],
        ["translate", "trophy", [0, 120, 0], "trophy"],
        ["engrave", "trophy", "backNamePlate", "trophy"],
        ["export", "trophy", "{trophy_name}"]
    ]
}"""


def serveHammerforge(event):
    if event['httpMethod'] == 'POST':
        newTrophyOrder = {key: items[0] for key, items in parse_qs(event['body']).items()}
        print(newTrophyOrder)
        assert len(newTrophyOrder['event_venue']) < 32
        newTrophyOrder['event_date'] = datetime.fromisoformat(newTrophyOrder['event_date']).strftime('%m-%d-%Y')

        order_name = "|||||".join([term for term in newTrophyOrder.values()]) + '.stl'
        newSpaceforgeOrder = hammerTrophyOrderTemplate
        for pattern, replacement in {
            "{order_id}": str(uuid4()),
            "{trophy_name}": order_name,
            "{place}": "1st",
            "{event_venue}": newTrophyOrder['event_venue'],
            "{event_date}": newTrophyOrder['event_date']
        }.items():
            newSpaceforgeOrder = newSpaceforgeOrder.replace(pattern, replacement)

        print(f"Creating new Spaceforge Order: {newSpaceforgeOrder}")
        boto3.client("lambda").invoke(
            FunctionName="spaceforge-prod-sf",
            InvocationType="Event",
            Payload=newSpaceforgeOrder)
        return {
            "statusCode": 301,
            "headers": {"Location": f"/spaceforge/hammerforge/{order_name}"}
        }

    hammerforgeTemplate = import_html_template("hammerforge.html")
    return {
        "statusCode": 200,
        "headers": {"content-type": "text/html"},
        "body": hammerforgeTemplate
    }


def serveTrophyViewer(event):
    pathParameters = event.get('pathParameters', {})
    trophy_name = unquote(pathParameters.get('trophy_name', 'Ruckus Pizza-6/22/2022-3.stl'))
    venue, date = trophy_name.split("|||||")
    date = date.split('.')[0]

    try:
        boto3.resource('s3').Object('makurspace-static-assets', f'spaceforge_assets/{trophy_name}').load()
        trophyViewerTemplate = import_html_template('hammerforge_trophyviewer.html')
    except botocore.exceptions.ClientError:
        trophyViewerTemplate = import_html_template('hammerforge_pending_trophyviewer.html')

    for pattern, replacement in {
        "{trophy_name}": trophy_name,
        "{event_venue}": venue,
        "{event_date}": date
    }.items():
        trophyViewerTemplate = trophyViewerTemplate.replace(pattern, replacement)
    return {
        "statusCode": 200,
        "headers": {"content-type": "text/html"},
        "body": trophyViewerTemplate
    }


def lambda_handler(event, context):
    print(f"Received: {event}")
    resourcePath = event.get('resource', None)

    if resourcePath == '/spaceforge/assetviewer/{asset_name}':
        return serveAssetViewer(event)
    elif resourcePath == '/spaceforge':
        return serveSpaceforge(event)
    elif resourcePath == '/spaceforge/hammerforge':
        return serveHammerforge(event)
    elif resourcePath == '/spaceforge/hammerforge/{trophy_name}':
        return serveTrophyViewer(event)

    return {
        "statusCode": 504,
        "headers": {},
        "body": f"Unrecognized request: {event}"
    }


if __name__ == "__main__":
    lambda_handler({}, None)
