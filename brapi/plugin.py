import climmob.plugins as plugins
import climmob.plugins.utilities as u
from views import BRAPIServersView
from .helpers import check_integration


class BrAPI(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IConfig)
    plugins.implements(plugins.ISchema)
    plugins.implements(plugins.ITemplateHelpers)

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
            u.addFieldToProjectSchema("link_breedbase", "Link to a BreedBase"),
            u.addFieldToProjectSchema("breedbase_server", "BreedBase Server"),
            u.addFieldToProjectSchema("breedbase_api", "BreedBase API version"),
        ]

    def get_helpers(self):
        return {"check_integration": check_integration}
