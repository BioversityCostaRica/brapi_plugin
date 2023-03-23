from climmob.views.classes import publicView, privateView
from .brapi import send_study_data, send_trait_data, send_observations
from climmob.models import Project, mapFromSchema
import json
import os
from pyramid.httpexceptions import HTTPFound
from .oi_client import get_login_url, update_user_token
import datetime as dt


class BRAPIOILogin(privateView):
    def processView(self):
        login_url = get_login_url(self.request)
        self.returnRawViewResult = True
        return HTTPFound(login_url)


class BRAPIOICallBack(privateView):
    def processView(self):
        if self.request.method == "POST":
            data = self.getPostDict()
            _now = dt.datetime.now()  # or dt.datetime.now(dt.timezone.utc)
            _in_future_sec = _now + dt.timedelta(seconds=int(data["expires_in"]) - 10)
            user_data = {
                "breedbase_token": data["access_token"],
                "breedbase_token_expires_on": _in_future_sec.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
            update_user_token(self.request, self.user.login, user_data)
        return {}


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
