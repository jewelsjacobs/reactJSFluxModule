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


@bp.route('/sso/consumer/', methods=['POST'])
def sso_consumer():
    """Process a posted SAML assertion and log the user in if everything checks out."""
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

    # Some variables for later use.
    username = user_info[sso.constants.SAML_USERNAME]
    tenant_id = user_info[sso.constants.SAML_USER_ID]
    email = user_info[sso.constants.SAML_EMAIL]
    ddi = user_info[sso.constants.SAML_DDI]
    main_db_connection = Utility.get_main_db_connection(config)

    # Get ObjectRocket 'login' from identity tenant (for resource mapping).
    login = sso.get_login_from_identity_tenant(tenant_id, main_db_connection)
    if login is None:
        sso.add_identity_tenant_entry(tenant_id, ddi, email, main_db_connection)

    # Ensure the login exists in the users collection, and fetch the tenant object.
    login = sso.ensure_resource_login(tenant_id, email, main_db_connection)
    tenant = sso.get_tenant_by_tenant_id(tenant_id, main_db_connection)

    # Track that this session started as an SSO login.
    session['login'] = login
    session['username'] = username
    session['tenant_id'] = tenant_id
    session['sso'] = True

    if tenant.first_sso:
        return render_template('sso/migration_first_sso.html')

    # TODO(TheDodd): not sure if we actually need this.
    # # Ensure user has accepted MSA.
    # account = AccountManager(config).get_account(login)
    # if not account.accepted_msa:
    #     return redirect(url_for('msa'))

    return redirect(url_for('instances'))


@bp.route('/sso/migration_link_account', methods=['POST'])
def migration_link_account():
    """Link an ObjectRocket account with the SSO user's Reach account."""
    main_db_connection = Utility.get_main_db_connection(config)
    tenant = sso.get_tenant_by_tenant_id(session.get('tenant_id'), main_db_connection)
    if tenant is None or not tenant.first_sso:
        return redirect(url_for('instances'))

    # return render_template('sso/migration_link_account.html')
    return redirect(url_for('instances'))


@bp.route('/sso/migration_create_free_instance_confirm', methods=['POST'])
def migration_create_free_instance_confirm():
    """Present the create free instance confirmation page to the SSO user."""
    main_db_connection = Utility.get_main_db_connection(config)
    tenant = sso.get_tenant_by_tenant_id(session.get('tenant_id'), main_db_connection)
    if tenant is None or not tenant.first_sso:
        return redirect(url_for('instances'))

    return render_template('sso/migration_create_free_instance_confirm.html')


@bp.route('/sso/migration_create_free_instance', methods=['POST'])
def migration_create_free_instance():
    """Create a free instance for the SSO user."""
    main_db_connection = Utility.get_main_db_connection(config)
    tenant = sso.get_tenant_by_tenant_id(session.get('tenant_id'), main_db_connection)
    if tenant is None or not tenant.first_sso:
        return redirect(url_for('instances'))

    # return render_template('sso/migration_create_free_instance.html')
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


@bp.route('/sso/response/')
def slo_response():
    return 200
