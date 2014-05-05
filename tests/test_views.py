import json
import pytest

from conftest import get_instance
from flask import url_for

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


def test_sign_up(app_client, stripe_token):
    from viper import config as viper_config
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
                                       stripe_pub_key=viper_config.STRIPE_PUB_KEY,
                                       name=name,
                                       plan=plan,
                                       zone=zone,
                                       service_type=service_type,
                                       version=version,
                                       ),
                                   follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        response = client.post('/sign_up_finish',
                                   data=dict(
                                       stripe_token=stripe_token['id'],
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
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/msa')
        assert response.status_code == 200


def test_msa_disagree(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/msa_disagree')
        assert response.status_code == 200


def test_msa_agree(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/msa_agree', follow_redirects=True)
        assert response.status_code == 200


def test_instances_create(app_client):
    with app_client as client:
        client.post(url_for('sign_in'), data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(url_for('instances_create'))
        print(response.data)
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


def test_instance_stats(app_client):
    with app_client as client:
        client.post(url_for('sign_in'), data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(url_for('instance_stats', selected_instance=instance_name))
        print(response.data)
        assert response.status_code == 200


def test_error(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/error')
        print(response.data)
        assert response.status_code == 200


def test_root(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/')
        print(response.data)
        assert response.status_code == 302


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
    """Tests accessing a database."""
    with app_client as client:
        sign_in_url = url_for('sign_in')
        database_url = url_for('database', selected_instance=instance_name, selected_database=database_name)
        client.post(sign_in_url, data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(database_url, follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        response = client.post(database_url, follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_create_collection(app_client):
    """Tests collection creation."""
    # TODO: Needs test with shard keys
    with app_client as client:
        sign_in_url = url_for('sign_in')
        create_collection_url = url_for('create_collection', selected_instance=instance_name, selected_database=database_name)
        client.post(sign_in_url, data=dict(login=login, password=password), follow_redirects=True)
        response = client.post(create_collection_url, data=dict(collection=collection_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_collection(app_client):
    """Tests accessing a collection."""
    with app_client as client:
        sign_in_url = url_for('sign_in')
        collection_url = url_for('collection',
                                 selected_instance=instance_name,
                                 selected_database=database_name,
                                 selected_collection=collection_name)
        client.post(sign_in_url, data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(collection_url, follow_redirects=True)
        print(response.data)
        assert response.status_code == 200

        response = client.post(collection_url, follow_redirects=True)
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


def test_add_acl(app_client):
    cidr_mask = 'any'
    description = 'test'
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/add_acl/{}'.format(instance_name),
                                   data=dict(
                                       cidr_mask=cidr_mask,
                                       description=description,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_delete_acl(app_client):
    cidr_mask = '66.66.66.66'
    cidr_description = 'test_acl'
    instance = get_instance(login, instance_name)
    acl_id = instance.add_acl(cidr_mask, cidr_description)

    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/delete_acl/{}'.format(instance_name),
                                   data=dict(
                                       acl_id=acl_id,
                                ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


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


def test_set_credit_card(app_client, stripe_token):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/set_credit_card', data=dict(stripe_token=stripe_token['id']), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


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


def test_system_status(app_client):
    with app_client as client:
        client.post(url_for('sign_in'), data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(url_for('system_status'))
        print(response.data)
        assert response.status_code == 200


def test_notifications(app_client):
    with app_client as client:
        client.post(url_for('sign_in'), data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(url_for('notifications'))
        print(response.data)
        assert response.status_code == 200


def test_admin_instance_management(app_client):
    with app_client as client:
        client.post(url_for('sign_in'), data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(url_for('admin_instance_management'))
        print(response.data)
        assert response.status_code == 200


def test_admin_user_management(app_client):
    with app_client as client:
        client.post(url_for('sign_in'), data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(url_for('admin_user_management'))
        print(response.data)
        assert response.status_code == 200


def test_admin_status_management(app_client):
    with app_client as client:
        client.post(url_for('sign_in'), data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(url_for('admin_status_management'))
        print(response.data)
        assert response.status_code == 200


def test_admin_billing(app_client):
    with app_client as client:
        client.post(url_for('sign_in'), data=dict(login=login, password=password), follow_redirects=True)
        response = client.get(url_for('admin_billing'))
        print(response.data)
        assert response.status_code == 200


def test_admin_switch_user(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/user_management/switch_user', data=dict(switchuser=login),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


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


def test_admin_add_message(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/status_management/add_message',
                               data=dict(login=login, message='Test message'),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_admin_set_status(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/status_management/set_status',
                               data=dict(api=0, east=1, driver=2, network=0,  system=1, west=2),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_admin_inventory(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/admin/inventory')
        print(response.data)
        assert response.status_code == 200


def test_admin_revenue(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password))
        response = client.get('/admin/revenue')
        print(response.data)
        assert response.status_code == 200


def test_admin_customer_reports(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password))
        response = client.get('/admin/customer_reports')
        print(response.data)
        assert response.status_code == 200


def test_admin_export_customer_report(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password))
        response = client.get('/admin/customer_reports/export')
        print(response.data)
        assert response.status_code == 200


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


def test_admin(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.get('/admin')
        print(response.data)
        assert response.status_code == 302


def test_compact_instance(app_client):
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/{}/compact'.format(instance_name), follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_admin_create_instance(app_client):
    instance_name = 'admin_test_instance'
    plan = 5
    service_type = 'mongodb'
    version = '2.4.6'
    zone = 'US-West'
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('/admin/instance_management/create_instance'.format(instance_name),
                               data=dict(
                                   account_name=login,
                                   name=instance_name,
                                   plan=plan,
                                   service_type=service_type,
                                   version=version,
                                   zone=zone,
                               ),
                                follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


def test_clear_alarm(app_client, annunciator):
    alarm = annunciator.create_alarm('ACCOUNT_SIGNUP', instance_name, 'info', login, notify_once=True)
    alarm_id = alarm.id
    with app_client as client:
        client.post('/sign_in', data=dict(login=login, password=password), follow_redirects=True)
        response = client.post('clear_alarm',
                               data=dict(alarm_id=alarm_id),
                               follow_redirects=True)
        print(response.data)
        assert response.status_code == 200


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
