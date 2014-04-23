import json
import pytest

from fixtures import app_client, testdb

xfail = pytest.mark.xfail


# TODO: Move to settings file
login = 'ortest'
password = 'ortest'
password_reset = 'ortest_reset'
instance_name = 'test_instance'
instance_name_rename = 'test_instance_rename'
database_name = 'test_database'
database_user_01 = 'test_user_01'
database_password_01 = 'test_password_01'
database_user_02 = 'test_user_02'
database_password_02 = 'test_password_02'
collection_name = 'test_collection'
email = 'ortest@objectrocket.com'
phone = '5125555555'
zipcode = '78750'
company = 'test'
name = 'test'

# TODO: Import from config
STRIPE_API_KEY = "Dsi61JdIV3p0yOP2oPCVb55h1GlOzUYe"
STRIPE_PUB_KEY = "pk_itj1Y8XIDV7U60NxGd1QCDv7Awjd9"


def test_sign_up(app_client):
    plan = '5'
    service_type = 'mongodb'
    version = '2.4.6'
    zone = 'US-West'
    with app_client as client:
        response = client.post('/sign_up1',
                                   data=dict(
                                       login=login,
                                       password=password,
                                       email=email,
                                       name=name,
                                       company=company,
                                       phone=phone,
                                       zipcode=zipcode,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200
        response = client.post('/sign_up3',
                                   data=dict(
                                       stripe_pub_key=STRIPE_PUB_KEY,
                                       name=name,
                                       plan=plan,
                                       zone=zone,
                                       service_type=service_type,
                                       version=version,
                                       ),
                                   follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        # TODO: Move to fixture
        import stripe
        stripe.api_key = STRIPE_API_KEY

        stripe_response = stripe.Token.create(card={
            "number": '4242424242424242',
            "exp_month": 12,
            "exp_year": 2017,
            "cvc": '123'
        },
        )

        response = client.post('/sign_up_finish',
                                   data=dict(
                                       stripe_token=stripe_response['id'],
                                       name=name,
                                       plan=plan,
                                       zone=zone,
                                       service_type=service_type,
                                       version=version,
                                       ),
                                   follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_login(app_client):
    response = app_client.get('/sign_in')
    assert response.status_code == 200
    assert "Sign In" in response.data
    response = app_client.post('/sign_in', data=dict(login=login, password=login), follow_redirects=True)
    assert response.status_code == 200


def test_msa(app_client):
    with app_client as client:
        response = client.get('/msa')
        assert response.status_code == 200


def test_or_msa(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/or_msa')
        print(response.data)
        assert response.status_code == 200


def test_msa_disagree(app_client):
    with app_client as client:
        response = client.get('/msa_disagree')
        assert response.status_code == 200


def msa_agree(app_client):
    with app_client as client:
        response = client.get('/msa_agree')
        assert response.status_code == 200


def test_create_instance(app_client):
    plan = '5'
    service_type = 'mongodb'
    version = '2.4.6'
    zone = 'US-West'
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/create_instance',
                                   data=dict(
                                       name=instance_name,
                                       plan=plan,
                                       service_type=service_type,
                                       version=version,
                                       zone=zone,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_error(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/error')
        print(response.data)
        assert response.status_code == 200


def test_default(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/')
        print(response.data)
        assert response.status_code == 200

        response = client.post('/')
        print(response.data)
        assert response.status_code == 200

        response = client.get('/{}'.format(instance_name))
        print(response.data)
        assert response.status_code == 200

        response = client.post('/{}'.format(instance_name))
        print(response.data)
        assert response.status_code == 200


def test_create_instance_user(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/create_instance_user/{}'.format(instance_name),
                                   data=dict(
                                       username=database_user_01,
                                       password=database_password_01,
                                       database_name=database_name,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        response = client.post('/create_instance_user/{}/{}'.format(instance_name, database_name),
                                   data=dict(
                                       username=database_user_02,
                                       password=database_password_02,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_delete_instance_user(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/delete_instance_user/{}/{}/{}'.format(instance_name, database_name, database_user_01),
                              follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        response = client.post('/delete_instance_user/{}/{}/{}'.format(instance_name, database_name, database_user_02),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


# @app.route('/copy_database/<selected_instance>', methods=['GET', 'POST'])
@xfail(reason="Test not implemented.")
def test_copy_database(app_client):
    # connect_string = request.form['connect_string']
    # database = request.form['database']
    # username = request.form['username']
    # password = request.form['password']
    pass


def test_instances(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/instances')
        print(response.data)
        assert response.status_code == 200


def test_instance_details(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/instances/{}'.format(instance_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        response = client.post('/instances/{}'.format(instance_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200



def test_database(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/instances/{}/{}'.format(instance_name, database_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        response = client.post('/instances/{}/{}'.format(instance_name, database_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_create_collection(app_client):
    # TODO: Needs test with shard keys
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/create_collection/{}/{}'.format(instance_name, database_name),
                               data=dict(
                                   collection=collection_name,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_collection(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/instances/{}/{}/{}'.format(instance_name, database_name, collection_name),
                              follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        response = client.post('/instances/{}/{}/{}'.format(instance_name, database_name, collection_name),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_cluster(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/instances/{}/cluster'.format(instance_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        response = client.post('/instances/{}/cluster'.format(instance_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_add_shard(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/add_shard/{}'.format(instance_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_rename_instance(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/rename_instance',
                                   data=dict(
                                       current_name=instance_name,
                                       new_name=instance_name_rename,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        # TODO: Can remove extra rename post when tests are decoupled
        response = client.post('/rename_instance',
                                   data=dict(
                                       current_name=instance_name_rename,
                                       new_name=instance_name,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_create_index(app_client):
    all_index_keys = '{"test_index_desc":"-1","test_index_asc":"1"}'
    background = 'true'
    name = 'test_indexes'
    sort_order = '1'
    unique = 'true'

    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/create_index/{}/{}/{}'.format(instance_name, database_name, collection_name),
                                   data=dict(
                                       all_index_keys = all_index_keys,
                                       background = background,
                                       name=name,
                                       sort_order=sort_order,
                                       unique=unique,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_messages(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/messages')
        print(response.data)
        assert response.status_code == 200


def test_account(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/account')
        print(response.data)
        assert response.status_code == 200


def test_external(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/external')
        print(response.data)
        assert response.status_code == 302


def test_new_relic(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/external/new_relic')
        print(response.data)
        assert response.status_code == 200


def test_add_new_relic_key(app_client):
    new_relic_key = 'A' * 40
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/external/add_new_relic_key', data=dict(new_relic_key=new_relic_key),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_delete_new_relic_key(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/external/delete_new_relic_key', follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_amazon(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/external/amazon')
        print(response.data)
        assert response.status_code == 200


def test_add_ec2_settings(app_client, monkeypatch):

    monkeypatch.setattr("viper.aws.AWSManager.validate_credentials", lambda(x): True)

    ec2_access_key = 'test_key'
    ec2_secret_key = 'test_key'
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/external/add_ec2_settings', data=dict(ec2_access_key=ec2_access_key,
                                                                        ec2_secret_key=ec2_secret_key),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_delete_ec2_settings(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/external/delete_ec2_settings', follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_update_settings(app_client):
    auto_shard_key = 'on'
    autoadd_shard_threshold = '85'
    balancer = 'on'
    balancer_window = 'on'
    balancer_window_start = '23:00'
    balancer_window_stop = '05:00'
    create_acls_for_aws_ips = 'on'
    new_relic_monitoring = 'on'
    profiling_level = '1'
    stepdown_scheduled = 'on'
    stepdown_window_enabled = 'on'
    stepdown_window_end = '01/02/2015 10:00'
    stepdown_window_start = '01/01/2015 10:00'
    stepdown_window_weekly = 'on'
    weekly_compaction_enabled = 'on'

    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/update_settings/{}'.format(instance_name),
                               data=dict(
                                   auto_shard_key=auto_shard_key,
                                   autoadd_shard_threshold=autoadd_shard_threshold,
                                   balancer=balancer,
                                   balancer_window=balancer_window,
                                   balancer_window_start=balancer_window_start,
                                   balancer_window_stop=balancer_window_stop,
                                   create_acls_for_aws_ips=create_acls_for_aws_ips,
                                   new_relic_monitoring=new_relic_monitoring,
                                   profiling_level=profiling_level,
                                   stepdown_scheduled=stepdown_scheduled,
                                   stepdown_window_enabled=stepdown_window_enabled,
                                   stepdown_window_end=stepdown_window_end,
                                   stepdown_window_start=stepdown_window_start,
                                   stepdown_window_weekly=stepdown_window_weekly,
                                   weekly_compaction_enabled=weekly_compaction_enabled,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_shard_collection(app_client):
    all_shard_keys = json.dumps({'test': 'hashed'})
    create_indexes =  'true'
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/shard_collection/{}/{}/{}'.format(instance_name, database_name, collection_name),
                               data=dict(
                                   all_shard_keys=all_shard_keys,
                                   create_indexes=create_indexes,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_add_allowed(app_client):
    cidr_mask = 'any'
    description = 'test'
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/add_allowed/{}'.format(instance_name),
                                   data=dict(
                                       cidr_mask=cidr_mask,
                                       description=description,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


# @app.route('/delete_acl/<instance>/<acl_id>')
@xfail(reason="Test not implemented.")
def delete_acl(app_client):
    pass


def test_update_account_contact(app_client):
    company_update = '{}_update'.format(company)
    email_update = '{}_update'.format(email)
    name_update = '{} update'.format(name)
    phone_update = '555-555-5555'
    zipcode_update = '78749'
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/update_account_contact',
                               data=dict(
                                   company=company_update,
                                   email=email_update,
                                   name=name_update,
                                   phone=phone_update,
                                   zipcode=zipcode_update,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_update_password(app_client):
    # request.form[Constants.PASSWORD]
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/update_password',
                                   data=dict(
                                       password=password_reset,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        # TODO: Can remove second post when tests are decoupled
        response = client.post('/update_password',
                                   data=dict(
                                       password=password,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200



# @app.route('/set_credit_card', methods=['POST'])
@xfail(reason="Test not implemented.")
def test_set_credit_card(app_client):
    # billing_manager.set_credit_card(g.login, request.form['stripe_token'])
    # if 'returntarget' in request.form:
    #     return redirect(url_for(request.form['returntarget']))
    pass


def test_logout(app_client):
    with app_client as client:
        client.post('/logout', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/logout', follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        client.post('/logout', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/update_account_contact', follow_redirects=True)
        print(response.data)
        assert response.status_code == 200



# @app.route('/reset_password', methods=['GET', 'POST'])
@xfail(reason="Test not implemented.")
def test_reset_password(app_client):
    # login = request.form[Constants.LOGIN]
    # if 'confirmPassword' in request.form:
    #     token = request.form['token']
    # password = request.form[Constants.PASSWORD]
    pass

# @app.route('/silence_alarm')
@xfail(reason="Test not implemented.")
def test_silence_alarm(app_client):
    pass


def test_billing(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/billing')
        print(response.data)
        assert response.status_code == 200


# @app.route('/invoices/<invoice_id>')
@xfail(reason="Test not implemented.")
def test_show_invoice(app_client):
    pass


def test_docs(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/docs')
        print(response.data)
        assert response.status_code == 200


def test_changelog(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/changelog')
        print(response.data)
        assert response.status_code == 200


def test_faq(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/faq')
        print(response.data)
        assert response.status_code == 200


def test_api(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/api')
        print(response.data)
        assert response.status_code == 200


def test_gui(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/gui')
        print(response.data)
        assert response.status_code == 200


def test_support(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/support')
        print(response.data)
        assert response.status_code == 200


def test_admin_switch_user(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/user_management/switch_user', data=dict(switchuser=login),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


# @app.route('/admin/alarms', methods=['GET', 'POST'])
# @viper_isadmin
@xfail(reason="Test not implemented.")
def test_admin_alarms(app_client):
    pass


@xfail(reason="Test not implemented. Need to create a fixture for associated Stripe ID")
def test_admin_associate_user(app_client):
    # login = request.form['login']
    # customer_id = request.form['customer_id']
    pass


def test_admin_sync_user(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/billing/sync_user', data=dict(login=login), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


# @app.route('/admin/add_message', methods=['POST'])
# @viper_isadmin
@xfail(reason="Test not implemented.")
def test_admin_add_message(app_client):
    # login = request.form.get('login', None)
    # message = request.form.get('message', None)
    pass


# @app.route('/admin/set_status', methods=['GET','POST'])
# @viper_isadmin
@xfail(reason="Test not implemented.")
def test_admin_set_status(app_client):
    # status_manager = StatusManager()
    # for i in request.form:
    #     status_manager.set_status(i, int(request.form[i]))
    pass

# @app.route('/admin/node_map', methods=['GET'])
@xfail(reason="Test not implemented.")
def test_admin_node_map(app_client):
    pass


# @app.route('/admin/customer_report', methods=['GET'])
# @viper_isadmin
@xfail(reason="Test not implemented.")
def test_admin_customer_report(app_client):
    pass


def test_set_user_invoiced(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/billing/set_user_invoiced', data=dict(invoiced_user=login), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_set_invoice_amount(app_client):
    amount = 100
    currency = 'USD'
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/billing/set_invoiced_amount', data=dict(account_id=login,
                                                                             amount=amount,
                                                                             currency=currency), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_set_user_customplan(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/billing/set_user_customplan', data=dict(customplan_user=login),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


# @app.route('/admin/customer_export', methods=['GET'])
@xfail(reason="Test not implemented.")
def test_admin_download_customer_report(app_client):
    pass


# @app.route('/admin')
def test_admin(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/admin')
        print(response.data)
        assert response.status_code == 200


def test_alarms(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/instances/{}/alarms'.format(instance_name))
        print(response.data)
        assert response.status_code == 200


# @app.route('/<instance_name>/request_compaction', methods=['POST'])
@xfail(reason="Test not implemented.")
def request_compaction(app_client):
    pass


# @app.route('/admin_create_instance', methods=['POST'])
@xfail(reason="Test not implemented.")
def test_admin_create_instance(app_client):
    # account_name    = request.form['account_name']
    # name            = request.form['name']
    # plan_size_in_gb = int(request.form['plan'])
    # service_type    = request.form['service_type']
    # version         = request.form['version']
    # zone            = request.form['zone']
    pass

# @app.route('/<instance_name>/alarm/clear', methods=['POST'])
@xfail(reason="Test not implemented.")
def test_alarm_clear(app_client):
    # alarm_id = request.form['alarm_id']
    pass


# @app.route('/<instance_name>/alarm/clear/all', methods=['POST'])
@xfail(reason="Test not implemented.")
def test_alarm_clear_all(app_client):
    # alarms = json.loads(request.form['alarms'])
    pass


@xfail(reason="Test env needs support for replica set instances.")
def test_repair_database(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/instances/{}/repair'.format(instance_name),
                               data={
                                   'database-name': database_name,
                                   },
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_drop_database(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/drop_database',
                               data=dict(
                                   db=database_name,
                                   instance=instance_name,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_delete_instance(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/{}/delete'.format(instance_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_admin_remove_user(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/user_management/remove_user', data=dict(login=login),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200
