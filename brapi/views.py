from climmob.views.classes import publicView
from .brapi import send_study_data, send_trait_data, send_observations
from climmob.models import Project, mapFromSchema
import json
import os


class BRAPIServersView(publicView):
    def processView(self):
        user = "cquiros"
        project = "brapi2"

        repository_path = self.request.registry.settings.get("user.repository")
        brapi_file = os.path.join(repository_path, *[user, project, "brapi.json"])
        current_data = {}
        if os.path.exists(brapi_file):
            with open(brapi_file) as json_file:
                current_data = json.load(json_file)

        project_data = (
            self.request.dbsession.query(Project)
            .filter(Project.project_cod == project)
            .filter(Project.user_name == user)
            .first()
        )
        project_data = mapFromSchema(project_data)
        with open("/home/cquiros/input_data.json") as json_file:
            input_data = json.load(json_file)

            send_study_data(
                user,
                project,
                input_data,
                project_data["breedbase_crop"],
                project_data["breedbase_url"],
                current_data,
            )
            send_trait_data(input_data, project_data["breedbase_url"], current_data)
            send_observations(input_data, project_data["breedbase_url"], current_data)
            with open(brapi_file, "w") as outfile:
                json.dump(current_data, outfile)
        return {}
