"""Blueprint for Rackspace SSO control."""
import base64

from flask import abort
from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session

from gui import config as gui_config
from viper import config
from viper.ext import sso
from viper.account import AccountManager
from viper.utility import Utility

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
                return redirect(url_for('sign_in'))

        # Ensure this is an SSO session.
        if session['sso'] is not True:
            return redirect(url_for('sign_in'))

    # Handle POST requests.
    else:

        # Kill all session information when this route is posted to.
        session.clear()

        # Ensure posted SAML assertion is legitimate.
        try:
            encoded_saml_response = request.form.get('SAMLResponse', None)
            decoded_saml_response = base64.decodestring(encoded_saml_response)
            saml_response = sso.util.get_saml_response_from_string(decoded_saml_response)
            # FIXME(TheDodd): need to finish building out this validation.
            # sso.util.validate_saml_response(saml_response, decoded_saml_response)

            # Get user info from SAMLResponse.
            user_info = sso.util.get_user_info_from_name_id_serialization(saml_response)

        except Exception as ex:
            gui_config.log_exception(current_app, ex)
            return redirect(url_for('sign_in'))

        # Session keys for migration stages.
        session[sso.constants.SSO] = True
        session[sso.constants.USERNAME] = user_info[sso.constants.SAML_USERNAME]
        session[sso.constants.TENANT_ID] = user_info[sso.constants.SAML_USER_ID]
        session[sso.constants.EMAIL] = user_info[sso.constants.SAML_EMAIL]
        session[sso.constants.DDI] = user_info[sso.constants.SAML_DDI]

    # Ensure this user is still in the initial SSO phase.
    tenant_id = session[sso.constants.TENANT_ID]
    main_db_connection = Utility.get_main_db_connection(config)
    tenant = sso.get_tenant_by_tenant_id(tenant_id, main_db_connection)
    if tenant and not tenant.initial_sso:
        return redirect(url_for('instances'))

    # User is still in the initial SSO phase.
    session[sso.constants.INITIAL_SSO] = True
    return render_template('sso/initial_sso.html')


@bp.route('/sso/link_mycloud_account', methods=['GET', 'POST'])
def link_mycloud_account():
    """Link an ObjectRocket account with the SSO user's Reach account."""
    # Ensure user is in initial SSO phase.
    if session.get(sso.constants.INITIAL_SSO, False) is not True:
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
        # - form validation - client side
        # - if credentials valid on server side
            # - create tenant entry
            # - mark account as migrated in users table (migration)

        # login_to_link = request.form['login']

        # TODO(TheDodd): pop first sso session key.
        return redirect(url_for('instances'))


@bp.route('/sso/seamless_login', methods=['GET', 'POST'])
def seamless_login():
    """Seamlessly create an ObjectRocket account linked with the SSO user's Reach account."""
    # Ensure user is in initial SSO phase.
    if session.get(sso.constants.INITIAL_SSO, False) is not True:
        return redirect(url_for('instances'))

    # Handle GET request.
    if request.method == 'GET':
        return render_template('sso/seamless_login.html')

    # Handle POST request.
    else:

        # Get needed session variables.
        tenant_id = session[sso.constants.TENANT_ID]
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
        return redirect(url_for('instances'))


@bp.route('/sso/_idp_test/')
def sso_idp():
    """An endpoint for testing SAML flow in development mode."""
    if current_app.config['CONFIG_MODE'] != 'development':
        abort(404)

    namestring = ('Username={username},DDI={ddi},UserID={user_id},Email={email},AuthToken={auth_token}'
                  .format(username='thedodd', ddi='12345', user_id='54321', email='anthony.dodd@rackspace.com', auth_token='1kj2h3g4k1jh2g34'))

    saml_response = sso.util.create_saml_response(name=namestring, in_response_to='somerequest', url=sso.config.SSO_ACS_URL, session_id=None, attributes={})
    saml_response_xml = saml_response.to_string()
    base64_saml_response = base64.b64encode(saml_response_xml)

    context = {
        'send_to': saml_response.destination,
        'relay_state': '072k3j4h5bkj2345',
        'saml': base64_saml_response,
        'saml_xml': sso.util.pretty_xml(saml_response_xml),
        'field_name': 'SAMLResponse',
        'auto_submit': False
    }

    return render_template('sso/_sso_test.html', **context)


@bp.route('/slo/request/')
def slo_request():
    return 200


@bp.route('/slo/response/')
def slo_response():
    return 200
