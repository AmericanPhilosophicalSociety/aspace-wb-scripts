'''
Takes as input your Workbench output .csv with an added column for ArchivesSpace ref IDs. Uses this data to create digital objects via the AS API.
'''
import os
import csv
from dotenv import load_dotenv
import aspace_wb.utils.default_specs as c
from aspace_wb.scripts.create_aspace_dos import parse_args
from aspace_wb.utils import convert_data
from asnake.client import ASnakeClient
from asnake.jsonmodel import JM
import time

def do_dicts_from_nodes(NODES_FILE):
    dos = []
    nodes_path = os.path.join(c.METADATA_DIR, NODES_FILE)

    with open(nodes_path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
    
        for row in reader:
            # skip over any row without an AS ref
            try:
                if row["as_ref"]:
                    AS_DO_dict = convert_data.diglib_node_to_AS_DO(row["node_id"])

                    AS_DO_dict["digital_object_title"] = row["title"]
                    AS_DO_dict["as_ref"] = row["as_ref"]
                    # print(AS_DO_dict)

                    dos.append(AS_DO_dict)
                else:
                    print(f"Skipping over row: {row["title"]}. No as_ref entered.")
            except KeyError:
                print("Ensure as_ref column is present and try again.")

    # print(dos)
    return dos

def set_up_client():
    # load environment and set variables
    load_dotenv()

    username = os.environ.get('API_WRITE_USERNAME')
    password = os.environ.get('API_WRITE_PASSWORD')
    base_url = os.environ.get('ASPACE_URL')

    client = ASnakeClient(baseurl=base_url,
                        username=username,
                        password=password)
    client.authorize()

    # client = ASnakeClient()
    # client.authorize()

    return client

def link_do_to_object(as_ref, client, response):
    try:
        # Continuing from above, using the returned digital object URI
        do_uri = response["uri"]  # e.g., "/repositories/2/digital_objects/45"
        ao_uri = f"/repositories/2/archival_objects/{as_ref}"

        # Fetch the existing archival object JSON
        ao_json = client.get(ao_uri).json()

        # Append the new digital object instance
        ao_json["instances"].append(
            {"instance_type": "digital_object", "digital_object": {"ref": do_uri}}
        )

        # Save the updated archival object
        update_response = client.post(ao_uri, json=ao_json)
        print(f"Digital object linked to record: {update_response.uri}")
        # print(update_response.status_code)

        time.sleep(3)
    except Exception as e:
        print(f"WARNING - Digital object could not be linked to AS record {as_ref}. Do this manually.")

def post_dos(dos, client):
    for do in dos:
        digital_object = JM.digital_object(
            title=do["digital_object_title"],
            digital_object_id=do["digital_object_id"],
            publish=True,
            file_versions=[
                JM.file_version(
                    file_uri=do["file_version_file_uri"],
                    publish=True,
                    #TODO: is local_identifier needed here?
                )
            ],
        )
        # print(digital_object)

        response = client.post(
            f"/repositories/2/digital_objects", json=digital_object
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Created digital object, URI: {result['uri']}")

            time.sleep(3)

            link_do_to_object(do["as_ref"], client, result)
        else:
            print(f"Error {response.status_code}: {response.text}")

def run_script():
    NODES_FILE = parse_args()
    dos = do_dicts_from_nodes(NODES_FILE)
    client = set_up_client()
    post_dos(dos, client)


    #TESTING - confirm that client is working and get an example record with associated digital object
    # as_ref = "861662"
    # ao_uri = f"/repositories/2/archival_objects/{as_ref}"

    # ao_uri = "/repositories/2/digital_objects/134751"
    
    # client = ASnakeClient()
    # client.authorize()
    # ao_json = client.get(ao_uri).json()
    # print(ao_json)
