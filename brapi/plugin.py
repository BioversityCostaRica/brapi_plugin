import climmob.plugins as plugins
import climmob.plugins.utilities as u
from .views import BRAPIServersView
from .helpers import (
    check_integration,
    get_servers,
    get_crops,
    get_server_url,
    crop_exist,
)


class BrAPI(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IConfig)
    plugins.implements(plugins.ISchema)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IProject)

    def before_mapping(self, config):
        # We don't add any routes before the host application
        return []

    def after_mapping(self, config):
        # We add here a new route /json that returns a JSON
        custom_map = [
            u.addRoute("brapi_servers", "/brapi/servers", BRAPIServersView, "json")
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
        ]

    def get_helpers(self):
        return {
            "check_integration": check_integration,
            "get_servers": get_servers,
            "get_crops": get_crops,
        }

    def before_adding_project(self, request, user, project_data):
        _ = request.translate
        if "breedbase_link" in project_data.keys():
            project_data["breedbase_link"] = 1
            if project_data.get("breedbase_crop", None) is None:
                return False, _("You need to specify a BreedBase crop"), project_data
            if project_data.get("breedbase_server", None) is None:
                return False, _("You need to specify a BreedBase server"), project_data
            print("*********************88")
            print(project_data["breedbase_server"])
            print("*********************88")
            server_url = get_server_url(project_data["breedbase_server"])
            if server_url is None:
                return False, _("Server not found"), project_data
            if not crop_exist(project_data["breedbase_crop"]):
                return False, _("Crop not found"), project_data
            project_data["breedbase_url"] = server_url
        return True, "", project_data

    def after_adding_project(self, request, user, project_data):
        pass
