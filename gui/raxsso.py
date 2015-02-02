"""Blueprint for Rackspace SSO control."""
import base64
import logging

from flask import abort
from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session

from canon import constants as canon_constants
from gui import config as gui_config
from viper import config
from viper.ext import sso
from viper.account import AccountManager
from viper.utility import Utility

LOG = logging.getLogger(__name__)

# Build blueprint and alias for ease of use.
bp = raxsso_blueprint = Blueprint('rax', __name__, url_prefix='/rax')


@bp.route('/sso/consumer/', methods=['GET', 'POST'])
def sso_consumer():
    """Process a posted SAML assertion and log the user in if everything checks out."""
    # Handle GET request.
    if request.method == 'GET':

        # Ensure needed session keys are present.
        for key in (sso.constants.USERNAME, sso.constants.TENANT_ID, sso.constants.EMAIL, sso.constants.DDI, 'sso'):
            if key not in session:
                LOG.info('SSO: needed session key missing: "{}". Redirecting to sign_in. Session: {}.'.format(key, session.items()))
                return redirect(url_for('sign_in'))

        # Ensure this is an SSO session.
        if session['sso'] is not True:
            LOG.info('SSO: session did not start via SSO. Redirecting to sign_in. Session: {}.'.format(session.items()))
            return redirect(url_for('sign_in'))

    # Handle POST requests.
    else:

        # Kill all session information when this route is posted to.
        session.clear()

        try:
            # Decode and validate SAMLResponse.
            encoded_saml_response = request.form.get('SAMLResponse', None)
            decoded_saml_response = base64.decodestring(encoded_saml_response)
            saml_response = sso.util.validate_saml_response(decoded_saml_response)

            # Get user info from SAMLResponse.
            user_info = sso.util.get_user_info_from_name_id_serialization(saml_response)

        except Exception as ex:
            gui_config.log_exception(current_app, ex)
            LOG.info('SSO: exception in "{}": {}.'.format(request.url, ex))
            return redirect(url_for('sign_in'))

        # Session keys for migration stages.
        session[sso.constants.SSO] = True
        session[sso.constants.AUTH_TOKEN] = user_info[sso.constants.SAML_AUTH_TOKEN]
        session[sso.constants.DDI] = user_info[sso.constants.SAML_DDI]
        session[sso.constants.EMAIL] = user_info[sso.constants.SAML_EMAIL]
        session[sso.constants.TENANT_ID] = user_info[sso.constants.SAML_USER_ID]
        session[sso.constants.USERNAME] = user_info[sso.constants.SAML_USERNAME]

    # Ensure requesting user has sufficient privileges for SSO.
    tenant_id = session[sso.constants.TENANT_ID]
    auth_token = session[sso.constants.AUTH_TOKEN]
    if not sso.sso_allowed(tenant_id, auth_token):
        LOG.info('SSO: insufficient privileges to SSO for member of tenant: "{}" with auth_token: "{}". Redirecting to sign_in.'.format(tenant_id, auth_token))
        return redirect(url_for('sign_in'))

    # Fetch info on the tenant that is logging in.
    main_db_connection = Utility.get_main_db_connection(config)
    tenant = sso.get_tenant_by_tenant_id(tenant_id, main_db_connection)

    # If tenant is not in the initial SSO phase, log them in directly.
    username = session[sso.constants.USERNAME]
    if tenant and not tenant.initial_sso:
        login = tenant.resource_login
        session[sso.constants.LOGIN] = login
        LOG.info('SSO: directly logging in user. Tenant ID: "{}"; Username: "{}"; Resource login: "{}".'.format(tenant_id, username, login))
        return redirect(url_for('instances'))

    # User is still in the initial SSO phase.
    session[sso.constants.INITIAL_SSO] = True
    LOG.info('SSO: user proceeding to initial SSO phase. Tenant ID: "{}"; Username: "{}".'.format(tenant_id, username))
    return render_template('sso/initial_sso.html')


@bp.route('/sso/link_mycloud_account', methods=['GET', 'POST'])
def link_mycloud_account():
    """Link an ObjectRocket account with the SSO user's Reach account."""
    # Ensure user is in initial SSO phase.
    if session.get(sso.constants.INITIAL_SSO, False) is not True:
        LOG.info('SSO: session is not in initial SSO phase. Redirecting to instances. Session: {}.'.format(session.items()))
        return redirect(url_for('instances'))

    # Handle GET request.
    if request.method == 'GET':

        # Look for an account which may be the SSO user's ... and hint towards it.
        account = AccountManager(config).get_account(session[sso.constants.USERNAME])
        matching_login = getattr(account, sso.constants.LOGIN, '')
        context = {'matching_login': matching_login}
        return render_template('sso/link_mycloud_account.html', **context)

    # Handle POST request.
    else:

        # Get form data and attempt to auth against the account.
        login_to_link = request.form['login-to-link']
        login_to_link_password = request.form['login-to-link-password']
        account = AccountManager(config).authenticate(login_to_link, login_to_link_password)

        # If auth has failed, just send user back with same username pre-populated.
        if account is None:
            flash('Looks like that username & password combination is invalid.', canon_constants.STATUS_ERROR)
            context = {'matching_login': login_to_link, 'auth_failure': True}
            return render_template('sso/link_mycloud_account.html', **context)

        # Get needed session variables.
        tenant_id = session[sso.constants.TENANT_ID]
        username = session[sso.constants.USERNAME]
        email = session[sso.constants.EMAIL]
        ddi = session[sso.constants.DDI]

        # Add a tenant entry.
        main_db_connection = Utility.get_main_db_connection(config)
        sso.add_identity_tenant_entry(tenant_id, ddi, email, main_db_connection, resource_login=account.login)
        sso.migrate_existing_users_entry(account.login, tenant_id, main_db_connection)

        # This session is no longer in initial SSO phase.
        session[sso.constants.LOGIN] = login_to_link
        session.pop(sso.constants.INITIAL_SSO, None)
        sso.conclude_initial_sso(tenant_id, main_db_connection)
        LOG.info('SSO: legacy account "{}" linked with Identity tenant: "{}" by Identity user: "{}".'.format(account.login, tenant_id, username))
        return redirect(url_for('instances'))


@bp.route('/sso/seamless_login', methods=['GET', 'POST'])
def seamless_login():
    """Seamlessly create an ObjectRocket account linked with the SSO user's Reach account."""
    # Ensure user is in initial SSO phase.
    if session.get(sso.constants.INITIAL_SSO, False) is not True:
        LOG.info('SSO: session is not in initial SSO phase. Redirecting to instances. Session: {}.'.format(session.items()))
        return redirect(url_for('instances'))

    # Handle GET request.
    if request.method == 'GET':
        return render_template('sso/seamless_login.html')

    # Handle POST request.
    else:

        # Get needed session variables.
        tenant_id = session[sso.constants.TENANT_ID]
        username = session[sso.constants.USERNAME]
        email = session[sso.constants.EMAIL]
        ddi = session[sso.constants.DDI]

        # Get ObjectRocket 'login' from identity tenant (a 'resource login' for resource mapping).
        main_db_connection = Utility.get_main_db_connection(config)
        resource_login = sso.get_login_from_identity_tenant(tenant_id, main_db_connection)
        if resource_login is None:
            sso.add_identity_tenant_entry(tenant_id, ddi, email, main_db_connection)

        # Ensure the login exists in the users collection, and fetch the tenant object.
        login = sso.ensure_resource_login(tenant_id, email, main_db_connection)

        # This session is no longer in initial SSO phase.
        session[sso.constants.LOGIN] = login
        session.pop(sso.constants.INITIAL_SSO, None)
        sso.conclude_initial_sso(tenant_id, main_db_connection)
        LOG.info('SSO: new account created for Identity user: "{}" of tenant: "{}". Resource login: "{}".'.format(username, tenant_id, login))
        return redirect(url_for('instances'))


@bp.route('/sso/_idp_test/', methods=['GET', 'POST'])
def sso_idp():
    """An endpoint for testing SAML flow in development mode."""
    if current_app.config['CONFIG_MODE'] != 'development':
        abort(404)

    context = {}
    if request.method == 'POST':
        # Get the posted request and add it to the context.
        encoded_saml_request = request.form.get('SAMLRequest')
        saml_request_xml = base64.decodestring(encoded_saml_request)
        context['saml_request'] = sso.util.pretty_xml(saml_request_xml)

    # Generate a SAMLResponse for development testing.
    namestring = ('Username={username},DDI={ddi},UserID={user_id},Email={email},AuthToken={auth_token}'
                  .format(username='ortest', ddi='12345', user_id='54321', email='anthony@objectrocket.com', auth_token='1kj2h3g4k1jh2g34'))
    saml_response = sso.util.create_saml_response(name=namestring, in_response_to='somerequest', url=sso.config.SSO_ACS_URL, session_id=None, attributes={})
    saml_response_xml = saml_response.to_string()
    encoded_saml_response = base64.b64encode(saml_response_xml)

    context.update({
        'send_to': saml_response.destination,
        'relay_state': '072k3j4h5bkj2345',
        'encoded_saml_response': encoded_saml_response,
        'saml_xml': sso.util.pretty_xml(saml_response_xml)
    })

    return render_template('sso/_sso_test.html', **context)


@bp.route('/cloud/<tenant_id>/account/')
def sso_idp_account_settings(tenant_id):
    """An endpoint for testing SSO IdP Account Settings page."""
    if current_app.config['CONFIG_MODE'] != 'development':
        abort(404)

    main_db_connection = Utility.get_main_db_connection(config)
    tenant = sso.get_tenant_by_tenant_id(tenant_id, main_db_connection)
    return render_template('sso/_sso_idp_account_settings.html', tenant=tenant)


@bp.route('/sso/logout/request/', methods=['POST'])
def sso_logout_request():
    """Validate a LogoutRequest from Reach and respond appropriately.

    Reach will send a LogoutRequest as the BODY of the request. If the request is valid, clear the
    session of the specified user and respond with a SAML LogoutResponse.
    """
    # TODO(TheDodd): needs to be activated when Reach is ready to send us SLO requests.
    if True:
        return 200

    try:
        # Decode and validate a SAML LogoutRequest.
        encoded_saml_logout_request = request.body
        decoded_saml_logout_request = base64.decodestring(encoded_saml_logout_request)
        saml_logout_request = sso.util.validate_saml_logout_request(decoded_saml_logout_request)

        # Get some needed variables.
        username = saml_logout_request.name_id.text
        issuer = saml_logout_request.issuer.text
        sso.kill_user_session(username)
    except Exception as ex:
        gui_config.log_exception(current_app, ex)
        abort(401)

    logout_response = sso.util.create_saml_logout_response(in_response_to=issuer)
    encoded_logout_response = base64.b64encode(logout_response.to_string())
    return encoded_logout_response, 200


@bp.route('/sso/logout/response/', methods=['POST'])
def sso_logout_response():
    """Validate and confirm a LogoutResponse from Reach.

    After a logout is requested, Reach will log the user out and POST a SAML LogoutResponse to
    this endpoint. The LogoutResponse will be in the BODY of the request. This endpoint should
    respond with a 200 as long as the request is valid. No content needs to be returned.

    This serves very little purpose.
    """
    # TODO(TheDodd): needs to be activated when Reach is ready to send us SLO requests.
    if True:
        return 200

    try:
        # Decode and validate a SAML LogoutResponse.
        encoded_saml_logout_response = request.body
        decoded_saml_logout_response = base64.decodestring(encoded_saml_logout_response)
        sso.util.validate_saml_logout_response(decoded_saml_logout_response)
    except Exception as ex:
        gui_config.log_exception(current_app, ex)
        abort(401)

    return 200
