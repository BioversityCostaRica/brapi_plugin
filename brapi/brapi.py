from .helpers import get_crop_desc
import json
import datetime
import requests


def find_breed_base_variable(current_data, variable_code):
    for a_variable in current_data["variables"]:
        parts = a_variable["variable_id"].split("-")
        if parts[2] == variable_code:
            return a_variable["observationVariableDbId"]
    return None


def send_observations(project_data, server_url, current_data):
    headers = {"Content-Type": "application/json", "accept": "application/json"}
    assessments = []
    for an_assessment in project_data["assessments"]:
        assessments.append({"code": an_assessment["code"], "variables": []})
    for an_assessment in assessments:
        for a_field in project_data["specialfields"]:
            if a_field["type"] == "Characteristic":
                if a_field["name"].find(an_assessment["code"]) >= 0:
                    parts = a_field["name"].split("_")
                    variable_code = parts[2]
                    var_found = False
                    for a_variable in an_assessment["variables"]:
                        if a_variable["code"] == variable_code:
                            a_variable["elements"].append(a_field)
                            var_found = True
                            break
                    if not var_found:
                        an_assessment["variables"].append(
                            {
                                "code": variable_code,
                                "breed_base_variable": find_breed_base_variable(
                                    current_data, variable_code
                                ),
                                "elements": [a_field],
                            }
                        )

    study_code = "CLIMMOB_{}_{}".format(
        project_data["project"]["user_name"], project_data["project"]["project_cod"]
    )
    study_id = current_data["studyDbId"]

    observations = []
    for a_row in project_data["data"]:
        observation_code = study_code + "|" + a_row["REG_qst162"]
        package_info = project_data["packages"][int(a_row["REG_qst162"]) - 1]
        for an_assessment in assessments:
            observation_code = observation_code + "|" + an_assessment["code"]
            for a_variable in an_assessment["variables"]:
                option_left = [1, 2, 3]
                variable_neutral = ""
                breed_base_variable_neutral = ""
                for a_element in a_variable["elements"]:
                    if a_element["name"].find("_pos") >= 0:
                        variable_neutral = a_element["name"].replace("_pos", "_neutral")
                    breed_base_variable_neutral = a_variable["breed_base_variable"]
                    observation_id = observation_code + "|" + a_element["name"]
                    observations.append(
                        {
                            "name": observation_id,
                            "date": a_row[
                                "ASS" + an_assessment["code"] + "__submitted_date"
                            ].replace(" ", "T")
                            + "Z",
                            "studyDbId": study_id,
                            "breed_base_variable": a_variable["breed_base_variable"],
                            "value": a_row[a_element["name"]],
                            "variety": package_info["comps"][
                                a_row[a_element["name"]] - 1
                            ]["technologies"][0]["alias_name"],
                        }
                    )
                    option_left.remove(a_row[a_element["name"]])
                observations.append(
                    {
                        "name": observation_code + "|" + variable_neutral,
                        "date": a_row[
                            "ASS" + an_assessment["code"] + "__submitted_date"
                        ].replace(" ", "T")
                        + "Z",
                        "studyDbId": study_id,
                        "breed_base_variable": breed_base_variable_neutral,
                        "value": option_left[0],
                        "variety": package_info["comps"][option_left[0] - 1][
                            "technologies"
                        ][0]["alias_name"],
                    }
                )

    observation_dict = {
        "germplasmName": "A0000003",
        "observationTimeStamp": "2021-11-16T01:59:37.433Z",
        "observationVariableDbId": "c403d107",
        "studyDbId": "ef2829db",
        "value": "2.3",
    }

    current_observations = current_data.get("observations", [])
    for an_observation in observations:
        observation_db_id = None
        for a_current_observation in current_observations:
            if a_current_observation["name"] == an_observation["name"]:
                observation_db_id = a_current_observation.get("observationDbId", None)
                break

        observation_data = observation_dict
        observation_data["germplasmName"] = an_observation["variety"]
        observation_data["observationTimeStamp"] = an_observation["date"]
        observation_data["observationVariableDbId"] = an_observation[
            "breed_base_variable"
        ]
        observation_data["studyDbId"] = an_observation["studyDbId"]
        if an_observation["name"].find("_pos") >= 0:
            observation_data["value"] = "Best"
        if an_observation["name"].find("_neg") >= 0:
            observation_data["value"] = "Worst"
        if an_observation["name"].find("_neutral") >= 0:
            observation_data["value"] = "Neutral"
        if observation_db_id is None:
            response = requests.post(
                "{}/observations".format(server_url),
                data=json.dumps([observation_data]),
                headers=headers,
            )
            if response.status_code == 200:
                data = json.loads(response.text)
                an_observation["observationDbId"] = data["result"]["data"][0][
                    "observationDbId"
                ]
            else:
                print("*****************Observation POST")
                print(response.status_code)
                print(response.text)
                print("*****************Observation POST")
                return
        else:
            response = requests.put(
                "{}/observations/{}".format(server_url, observation_db_id),
                data=json.dumps(observation_data),
                headers=headers,
            )
            if response.status_code != 200:
                print("*****************Observation PUT")
                print(response.status_code)
                print(response.text)
                print("*****************Observation PUT")
                return

    current_data["observations"] = observations


def send_trait_data(project_data, server_url, current_data):
    headers = {"Content-Type": "application/json", "accept": "application/json"}
    # - TRICOT Traits - One for each question type ranking of options
    trait_dict = {
        "traitClass": "TRICOT",
        "traitDescription": "The height of the plant",
        "additionalInfo": {},
        "traitName": "Height",
        "externalReferences": [
            {
                "referenceID": "{}-{}".format(
                    project_data["project"]["user_name"],
                    project_data["project"]["project_cod"],
                ),
                "referenceSource": "CLIMMOB-PROJECT",
            },
            {
                "referenceID": "{}".format(project_data["project"]["climmob-server"]),
                "referenceSource": "CLIMMOB-SERVER",
            },
        ],
    }
    for a_question in project_data["questions"]:
        if a_question["question_dtype"] == 9:
            trait_id = (
                "TRICOT"
                + "-"
                + a_question["user_name"]
                + "-"
                + str(a_question["question_code"])
            )
            trait_db_id = None

            if "traits" in current_data.keys():
                if trait_id in current_data["traits"].keys():
                    trait_db_id = current_data["traits"][trait_id]
            else:
                current_data["traits"] = {}

            a_trait = trait_dict
            a_trait["traitName"] = a_question["question_name"]
            a_trait["traitDescription"] = a_question["question_desc"]

            for key, value in a_question.items():
                a_trait["additionalInfo"][key] = value

            if trait_db_id is None:
                response = requests.post(
                    "{}/traits".format(server_url),
                    data=json.dumps([a_trait]),
                    headers=headers,
                )
                if response.status_code == 200:
                    data = json.loads(response.text)
                    current_data["traits"][trait_id] = data["result"]["data"][0][
                        "traitDbId"
                    ]
                else:
                    print("*****************Trait POST")
                    print(response.status_code)
                    print(response.text)
                    print("*****************Trait POST")
                    return
            else:
                response = requests.put(
                    "{}/traits/{}".format(server_url, trait_db_id),
                    data=json.dumps(a_trait),
                    headers=headers,
                )
                if response.status_code != 200:
                    print("*****************Trait PUT")
                    print(response.status_code)
                    print(response.text)
                    print("*****************Trait PUT")
                    return

    # - TRICOT Method. Only one

    if "method" not in current_data.keys():
        response = requests.post(
            "{}/methods".format(server_url),
            data=json.dumps([{"methodClass": "TRICOT", "methodName": "TRICOT"}]),
            headers=headers,
        )
        if response.status_code == 200:
            data = json.loads(response.text)
            current_data["method"] = data["result"]["data"][0]["methodDbId"]
        else:
            print("*****************Method POST")
            print(response.status_code)
            print(response.text)
            print("*****************Method POST")
            return
    else:
        response = requests.put(
            "{}/methods/{}".format(server_url, current_data["method"]),
            data=json.dumps({"methodClass": "TRICOT", "methodName": "TRICOT"}),
            headers=headers,
        )
        if response.status_code != 200:
            print("*****************Method PUT")
            print(response.status_code)
            print(response.text)
            print("*****************Method PUT")
            return

    # - TRICOT scale. Only one
    if "scale" not in current_data.keys():
        response = requests.post(
            "{}/scales".format(server_url),
            data=json.dumps(
                [
                    {
                        "dataType": "Numerical",
                        "decimalPlaces": 0,
                        "scaleName": "TRICOT Ranking",
                    }
                ]
            ),
            headers=headers,
        )
        if response.status_code == 200:
            data = json.loads(response.text)
            current_data["scale"] = data["result"]["data"][0]["scaleDbId"]
        else:
            print("*****************Scale POST")
            print(response.status_code)
            print(response.text)
            print("*****************Scale POST")
            return
    else:
        response = requests.put(
            "{}/scales/{}".format(server_url, current_data["scale"]),
            data=json.dumps(
                {
                    "dataType": "Numerical",
                    "decimalPlaces": 0,
                    "scaleName": "TRICOT Ranking",
                }
            ),
            headers=headers,
        )
        if response.status_code != 200:
            print("*****************Scale PUT")
            print(response.status_code)
            print(response.text)
            print("*****************Scale PUT")
            return

    # TRICOT variables. One for each question type ranking of options

    crop_desc = get_crop_desc(project_data["project"]["breedbase_crop"])
    variable_dict = {
        "commonCropName": "{}".format(crop_desc),
        "language": "en",
        "additionalInfo": {},
        "method": {"methodDbId": "{}".format(current_data["method"])},
        "observationVariableName": "Variable Name",
        "scale": {"scaleDbId": "{}".format(current_data["scale"])},
        "scientist": "{}".format(project_data["project"]["project_pi"]),
        "submissionTimestamp": "{}".format(
            datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
        "externalReferences": [
            {
                "referenceID": "{}-{}".format(
                    project_data["project"]["user_name"],
                    project_data["project"]["project_cod"],
                ),
                "referenceSource": "CLIMMOB-PROJECT",
            },
            {
                "referenceID": "{}".format(project_data["project"]["climmob-server"]),
                "referenceSource": "CLIMMOB-SERVER",
            },
        ],
        "trait": {"traitDbId": "9b2e34f5"},
    }

    for a_question in project_data["questions"]:
        if a_question["question_dtype"] == 9:
            variable_id = (
                "TRICOT"
                + "-"
                + a_question["user_name"]
                + "-"
                + str(a_question["question_code"])
            )
            variable_data = variable_dict
            variable_data["trait"]["traitDbId"] = current_data["traits"][variable_id]
            variable_data["observationVariableName"] = a_question["question_name"]

            for key, value in a_question.items():
                variable_data["additionalInfo"][key] = value

            if "variables" in current_data.keys():
                variable_db_id = None
                for a_variable in current_data["variables"]:
                    if a_variable["variable_id"] == variable_id:
                        variable_db_id = a_variable["observationVariableDbId"]
                if variable_db_id is None:
                    response = requests.post(
                        "{}/variables".format(server_url),
                        data=json.dumps([variable_data]),
                        headers=headers,
                    )
                    if response.status_code == 200:
                        data = json.loads(response.text)
                        current_data["variables"].append(
                            {
                                "observationVariableDbId": data["result"]["data"][0][
                                    "observationVariableDbId"
                                ],
                                "variable_id": variable_id,
                            }
                        )
                    else:
                        print("*****************variables POST")
                        print(response.status_code)
                        print(response.text)
                        print("*****************variables POST")
                        return
                else:
                    variable_data = variable_dict
                    response = requests.put(
                        "{}/variables/{}".format(server_url, variable_db_id),
                        data=json.dumps(variable_data),
                        headers=headers,
                    )
                    if response.status_code != 200:
                        print("*****************variables PUT")
                        print(response.status_code)
                        print(response.text)
                        print("*****************variables PUT")
                        return
            else:
                current_data["variables"] = []
                response = requests.post(
                    "{}/variables".format(server_url),
                    data=json.dumps([variable_data]),
                    headers=headers,
                )
                if response.status_code == 200:
                    data = json.loads(response.text)
                    current_data["variables"].append(
                        {
                            "observationVariableDbId": data["result"]["data"][0][
                                "observationVariableDbId"
                            ],
                            "variable_id": variable_id,
                        }
                    )
                else:
                    print("*****************variables POST")
                    print(response.status_code)
                    print(response.text)
                    print("*****************variables POST")
                    return


def send_study_data(user, project, project_data, crop, server_url, current_data):
    crop_desc = get_crop_desc(crop)
    start_date = project_data["project"]["project_creationdate"]
    start_date = start_date.replace(" ", "T") + "Z"
    with open("/home/cquiros/output.json", "w") as twitterDataFile:
        json.dump(project_data, twitterDataFile, indent=4)
    study_dict = {
        "active": "true",
        "commonCropName": crop_desc,
        "additionalInfo": {},
        "contacts": [
            {
                "email": "{}".format(project_data["project"]["project_piemail"]),
                "instituteName": "CLIMMOB",
                "name": "{}".format(project_data["project"]["project_pi"]),
                "type": "PI",
            }
        ],
        "externalReferences": [
            {
                "project_id": "CLIMMOB_{}_{}".format(user, project),
                "referenceSource": "CLIMMOB",
            },
        ],
        "documentationURL": "https://climmob.net",
        "endDate": "2021-11-09T14:29:23.075Z",
        "experimentalDesign": {
            "PUI": "TRICOT",
            "description": "The experiment has a TRICOT design",
        },
        "lastUpdate": {
            "timestamp": "{}".format(
                datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            "version": "{}".format(
                datetime.datetime.now().strftime("%Y_%m_%d %H:%M:%S")
            ),
        },
        "license": "MIT License",
        "locationName": "{}".format(project_data["project"]["project_cnty"]),
        "observationLevels": [
            {"levelName": "field", "levelOrder": 0},
            {"levelName": "block", "levelOrder": 1},
            {"levelName": "plot", "levelOrder": 2},
        ],
        "startDate": "{}".format(start_date),
        "studyCode": "CLIMMOB_{}_{}".format(user, project),
        "studyDescription": "{}".format(project_data["project"]["project_abstract"]),
        "studyName": "{}".format(project_data["project"]["project_name"]),
        "studyType": "Phenotyping",
        "trialName": "ClimMob_{}_Trial".format(crop_desc),
    }
    for key, value in project_data["project"].items():
        study_dict["additionalInfo"][key] = value
    headers = {"Content-Type": "application/json", "accept": "application/json"}
    if not current_data:
        response = requests.post(
            "{}/studies".format(server_url),
            data=json.dumps([study_dict]),
            headers=headers,
        )
        if response.status_code == 200:
            data = json.loads(response.text)
            current_data["studyDbId"] = data["result"]["data"][0]["studyDbId"]
        else:
            print("*******************Study POST")
            print(response.status_code)
            print(response.text)
            print("*******************Study POST")
    else:
        response = requests.put(
            "{}/studies/{}".format(server_url, current_data["studyDbId"]),
            data=json.dumps(study_dict),
            headers=headers,
        )
        if response.status_code != 200:
            print("*******************Study PUT")
            print(study_dict)
            print(response.status_code)
            print(response.text)
            print("*******************Study PUT")
