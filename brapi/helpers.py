def check_integration(user, project):
    return True


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
        if a_server["code"] is server_code:
            return a_server["url"]
    return None


def get_crops():
    return [{"code": "maize", "name": "Maize"}, {"code": "beans", "name": "Beans"}]


def crop_exist(crop_code):
    crops = get_crops()
    for a_crop in crops:
        if a_crop["code"] == crop_code:
            return True
    return False
