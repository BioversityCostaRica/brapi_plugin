import climmob.plugins as plugins
import climmob.plugins.utilities as u
from climmob.models import Project, mapFromSchema
from .views import BRAPISynch, BRAPIOILogin, BRAPIOICallBack
from .helpers import (
    check_integration,
    get_servers,
    get_crops,
    get_server_url,
    crop_exist,
    token_is_valid,
)
from .brapi import send_study_data
import json


class BrAPI(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IConfig)
    plugins.implements(plugins.ISchema)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IProject)
    plugins.implements(plugins.IResource)

    def before_mapping(self, config):
        # We don't add any routes before the host application
        return []

    def after_mapping(self, config):
        # We add here a new route /json that returns a JSON
        custom_map = [
            u.addRoute(
                "brapi_synchronize", "/breedbase/synch/{project}", BRAPISynch, "json"
            ),
            u.addRoute("brapi_oi_login", "/breedbase/login", BRAPIOILogin, None),
            u.addRoute(
                "brapi_oi_callback",
                "/breedbase/callback",
                BRAPIOICallBack,
                "oic/get_token.jinja2",
            ),
        ]
        return custom_map

    def update_config(self, config):
        # We add here the templates of the plugin to the config
        u.addTemplatesDirectory(config, "templates")
        u.addStaticView(config, "brapi", "static")

    def update_schema(self, config):
        return [
            u.addFieldToProjectSchema("breedbase_link", "Link to a BreedBase"),
            u.addFieldToProjectSchema("breedbase_crop", "Main crop of the breedBase"),
            u.addFieldToProjectSchema("breedbase_server", "BreedBase Server"),
            u.addFieldToProjectSchema("breedbase_url", "BreedBase Server URL"),
            u.addFieldToProjectSchema("breedbase_license", "BreedBase License"),
            u.addFieldToProjectSchema("breedbase_login", "BreedBase Login required"),
            u.addFieldToUserSchema(
                "breedbase_token", "Last token used to authenticate"
            ),
            u.addFieldToUserSchema(
                "breedbase_token_expires_on", "Expire date for the token"
            ),
        ]

    def get_helpers(self):
        return {
            "check_integration": check_integration,
            "get_servers": get_servers,
            "get_crops": get_crops,
            "token_is_valid": token_is_valid,
        }

    def before_adding_project(self, request, user, project_data):
        _ = request.translate
        if "breedbase_link" in project_data.keys():
            project_data["breedbase_link"] = 1
            if project_data.get("breedbase_license", None) is None:
                return False, _("You need to specify a BreedBase license"), project_data
            if project_data.get("breedbase_crop", None) is None:
                return False, _("You need to specify a BreedBase crop"), project_data
            if project_data.get("breedbase_server", None) is None:
                return False, _("You need to specify a BreedBase server"), project_data
            server_url = get_server_url(project_data["breedbase_server"])
            if server_url is None:
                return False, _("BreedBase server not found"), project_data
            if not crop_exist(project_data["breedbase_crop"]):
                return False, _("BreedBase Crop not found"), project_data
            project_data["breedbase_url"] = server_url
            if "breedbase_login" in project_data.keys():
                project_data["breedbase_login"] = 1
            else:
                project_data["breedbase_login"] = 0
        else:
            project_data["breedbase_link"] = 0
            project_data["breedbase_crop"] = ""
            project_data["breedbase_server"] = ""
            project_data["breedbase_url"] = ""
            project_data["breedbase_license"] = ""
            project_data["breedbase_login"] = 0
        return True, ""

    def after_adding_project(self, request, user, project_data):
        pass

    def before_updating_project(self, request, user_name, project_id, project_data):
        print(project_data)
        _ = request.translate
        if "breedbase_link" in project_data.keys():
            project_data["breedbase_link"] = 1
            if project_data.get("breedbase_license", "") == "":
                return False, _("You need to specify a License"), project_data
            if project_data.get("breedbase_crop", None) is None:
                return False, _("You need to specify a BreedBase crop"), project_data
            if project_data.get("breedbase_server", None) is None:
                return False, _("You need to specify a BreedBase server"), project_data
            server_url = get_server_url(project_data["breedbase_server"])
            if server_url is None:
                return False, _("BreedBase server not found"), project_data
            if not crop_exist(project_data["breedbase_crop"]):
                return False, _("BreedBase Crop not found"), project_data
            project_data["breedbase_url"] = server_url
            if "breedbase_login" in project_data.keys():
                project_data["breedbase_login"] = 1
            else:
                project_data["breedbase_login"] = 0
        else:
            project_data["breedbase_link"] = 0
            project_data["breedbase_crop"] = ""
            project_data["breedbase_server"] = ""
            project_data["breedbase_url"] = ""
            project_data["breedbase_license"] = ""
            project_data["breedbase_login"] = 0
        return (
            True,
            "",
        )

    def after_updating_project(self, request, user_name, project_id, project_data):
        pass

    def before_returning_project_context(self, request, context):
        return context

    # # IReport
    # def on_generate(self, request, user, project, input_data):
    #     project_data = (
    #         request.dbsession.query(Project)
    #         .filter(Project.project_cod == project)
    #         .filter(Project.user_name == user)
    #         .first()
    #     )
    #     project_data = mapFromSchema(project_data)
    #
    #     with open("/home/cquiros/input_data.json", "w") as outfile:
    #         json.dump(input_data, outfile)

    # if "breedbase_link" in project_data.keys():
    #     if project_data["breedbase_link"] == 1:
    #         send_study_data(user, project, input_data, project_data["breedbase_crop"], project_data["breedbase_url"])

    # IResource
    def add_libraries(self, config):
        libraries = []
        libraries.append(u.addLibrary("brapi_resources", "fanstatic"))
        return libraries

    def add_js_resources(self, config):
        return [
            {
                "libraryname": "brapi_resources",
                "id": "jscookies",
                "file": "cookie/js.cookie.min.js",
                "depends": None,
            }
        ]

    def add_css_resources(self, config):
        return []
