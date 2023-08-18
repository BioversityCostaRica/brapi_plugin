from climmob.models import Project, mapFromSchema, Prjtech, Technology
from sqlalchemy import func
import datetime


def token_is_valid(expire_datetime):
    try:
        datetime_object = datetime.datetime.strptime(
            expire_datetime, "%Y-%m-%d %H:%M:%S"
        )
        if datetime_object >= datetime.datetime.now():
            return True
        else:
            return False
    except:
        return False


def check_integration(request, project_id):
    project_data = (
        request.dbsession.query(Project)
        .filter(Project.project_id == project_id)
        .first()
    )
    project_data = mapFromSchema(project_data)
    if "breedbase_link" in project_data.keys():
        if project_data["breedbase_link"] == 1:
            if (
                request.dbsession.query(func.count(Prjtech.tech_id))
                .filter(Prjtech.project_id == project_id)
                .scalar()
                > 0
            ):
                techs = (
                    request.dbsession.query(func.count(Technology.tech_id))
                    .filter(Technology.tech_id == Prjtech.tech_id)
                    .filter(Prjtech.project_id == project_id)
                    .filter(Technology.croptaxonomy_code == 0)
                    .scalar()
                )
                if techs == 0:
                    return 1
                else:
                    return 0
            else:
                return 2
    return -1


def get_crops():
    return [{"code": "cassava", "name": "Cassava", "server": "https://cassavabase.org"},
            {"code": "yam", "name": "Yam", "server": "https://yambase.org"}]


def get_crop_desc(crop_code):
    crops = get_crops()
    for a_crop in crops:
        if a_crop["code"] == crop_code:
            return a_crop["name"]
    return ""


def get_crop_server(crop_code):
    crops = get_crops()
    for a_crop in crops:
        if a_crop["code"] == crop_code:
            return a_crop["server"]
    return ""


def crop_exist(crop_code):
    crops = get_crops()
    for a_crop in crops:
        if a_crop["code"] == crop_code:
            return True
    return False
