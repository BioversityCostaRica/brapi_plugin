from climmob.models import Project, mapFromSchema, Prjtech, Technology
from sqlalchemy import func


def check_integration(request, user, project):
    project_data = (
        request.dbsession.query(Project)
        .filter(Project.project_cod == project)
        .filter(Project.user_name == user)
        .first()
    )
    project_data = mapFromSchema(project_data)
    if "breedbase_link" in project_data.keys():
        if project_data["breedbase_link"] == 1:
            if (
                request.dbsession.query(func.count(Prjtech.tech_id))
                .filter(Prjtech.project_cod == project)
                .filter(Prjtech.user_name == user)
                .scalar()
                > 0
            ):
                techs = (
                    request.dbsession.query(func.count(Technology.tech_id))
                    .filter(Technology.tech_id == Prjtech.tech_id)
                    .filter(Prjtech.user_name == user)
                    .filter(Prjtech.project_cod == project)
                    .filter(Technology.tech_crop == 0)
                    .scalar()
                )
                if techs == 0:
                    return 1
                else:
                    return 0
            else:
                return 2
    return -1


breed_base_servers = [
    {
        "code": "test",
        "name": "Test server",
        "url": "https://test-server.brapi.org/brapi/v2/",
    },
    {
        "code": "cassavabase",
        "name": "NextGen Cassava Project",
        "url": "https://cassavabase.org/brapi/v2/",
    },
    {
        "code": "yambase",
        "name": "Africa Yam Project",
        "url": "https://yambase.org/brapi/v2/",
    },
]


def get_servers():
    return breed_base_servers


def get_server_url(server_code):
    for a_server in breed_base_servers:
        if a_server["code"] == server_code:
            return a_server["url"]
    return None


def get_crops():
    return [{"code": "maize", "name": "Maize"}, {"code": "beans", "name": "Beans"}]


def get_crop_desc(crop_code):
    crops = get_crops()
    for a_crop in crops:
        if a_crop["code"] == crop_code:
            return a_crop["name"]
    return ""


def crop_exist(crop_code):
    crops = get_crops()
    for a_crop in crops:
        if a_crop["code"] == crop_code:
            return True
    return False
