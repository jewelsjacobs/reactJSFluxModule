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

from viper import config
from viper.ext import sso
from viper.account import AccountManager
from viper.utility import Utility

# Build blueprint and alias for ease of use.
bp = Blueprint('rax', __name__, url_prefix='/rax')
raxsso_blueprint = bp


@bp.route('/sso/consumer/', methods=['POST'])
def sso_consumer():
    """Process a posted SAML assertion and log the user in if everything checks out."""
    # Ensure posted SAML assertion is legitimate.
    encoded_saml_response = request.form.get('SAMLResponse', None)
    saml_response = sso.util.decode_saml_response(encoded_saml_response)
    samlobj = sso.util.instantiate_saml_response_class(saml_response)
    if not samlobj:
        return redirect(url_for('sign_in'))

    # Get user info from SAMLResponse.
    user_info = sso.util.get_user_info_from_name_id_serialization(samlobj)
    if not user_info:
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
        login = sso.ensure_resource_login(tenant_id, email, main_db_connection)

    # Get the account object corresponding to the derived username.
    account = AccountManager(config).get_account(username)
    if account is None:
        # TODO(TheDodd): build out migration template with Drew.
        return render_template('sso/first_sso_migration.html')

    # If the account is not already migrated, send to migration page with name conflict.
    elif not account.migrated:
        # TODO(TheDodd): build out migration template with Drew.
        return render_template('sso/first_sso_migration.html', name_conflict=username)

    # The account is already migrated, so track that this session started as an SSO login.
    session['login'] = username
    session['sso_login'] = True

    # Ensure user has accepted MSA.
    if not account.accepted_msa:
        return redirect(url_for('msa'))

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


# @bp.route('/sso/_sso_test/')
# def sso_idp():
#     """An endpoint for testing SAML flow in development mode."""
#     if current_app.config.CONFIG_MODE != 'development':
#         abort(404)
#     return render_template('sso/_sso_test.html', name_conflict=username)


@bp.route('/slo/request/')
def slo_request():
    return 200


@bp.route('/sso/response/')
def slo_response():
    return 200
