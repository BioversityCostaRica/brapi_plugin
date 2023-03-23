from oic.oic import Client
from oic.utils.authn.client import ClientSecretBasic
from oic import rndstr
from climmob.models import User
from climmob.models.schema import mapToSchema


def get_login_url(request):
    client_id = request.registry.settings.get("brapi.client_id")
    client_secret = request.registry.settings.get("brapi.client_secret")
    redirect_uri = request.route_url("brapi_oi_callback")
    issuer_url = request.registry.settings.get("brapi.issuer_url")
    state = rndstr()
    nonce = rndstr()
    args = {
        "client_id": client_id,
        "response_type": ["id_token", "token"],
        "scope": ["openid"],
        "state": state,
        "nonce": nonce,
        "redirect_uri": redirect_uri,
    }
    client = Client(
        client_id=client_id,
        client_authn_method=ClientSecretBasic({"client_secret": client_secret}),
    )

    client.allow = {"issuer_mismatch": True}
    client.provider_config(issuer_url)

    auth_req = client.construct_AuthorizationRequest(request_args=args)
    login_url = auth_req.request(client.authorization_endpoint)
    return login_url


def update_user_token(request, user_name, data):
    mapped_data = mapToSchema(User, data)
    request.dbsession.query(User).filter(User.user_name == user_name).update(
        mapped_data
    )
