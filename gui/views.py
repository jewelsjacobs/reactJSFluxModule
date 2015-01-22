"""GUI application views."""
from __future__ import division

# STL imports.
import collections
import datetime
import json
import urllib
import re

# 3rd party imports.
import bson
import itsdangerous
import requests
import stripe

# 3rd party from imports.
from flask import abort, Response
from flask import flash, request, render_template, session, redirect, url_for, g
from flask_wtf import csrf
from functools import wraps
from jinja2.filters import do_filesizeformat as filesizeformat
from netaddr import IPNetwork, AddrFormatError
from pymongo.errors import ConnectionFailure, OperationFailure
from werkzeug.datastructures import ImmutableMultiDict
from urlparse import urlparse

# ObjectRocket from imports.
from canon import constants as canon_constants
from gui import forms
from viper import config
from viper import monitor
from viper import tokens
from viper.account import AccountManager
from viper.annunciator import Annunciator, Alarm
from viper.aws import AWSManager
from viper.billing import BillingManager, BillingException
from viper.checks.salesforce import send_signup_to_salesforce
from viper.constants import Constants
from viper.instance import InstanceManager
from viper.messages import MessageManager
from viper.mongo_instance import MongoDBInstanceException
from viper.notifier import Notifier
from viper.rackspace import RAXManager
from viper.remote_instance import ClientWrapper, SslConnectionFailure
from viper.remote_instance_manager import RemoteInstanceManager
from viper.replica import ReplicaException
from viper.status import StatusManager
from viper.utility import Host, InvalidHost, Utility

# Make app available in this scope.
from gui import app


# TODO: Refactor: Should move to a Utility lib
# -----------------------------------------------------------------------
# Viper Decorators
# -----------------------------------------------------------------------
def billing_enabled(func):
    """Decorator to test that the account has billing enabled."""
    @wraps(func)
    def internal(*args, **kwargs):
        account_manager = AccountManager(config)
        account = account_manager.get_account(g.login)
        if account.invoiced or account.stripe_account:
            return func(*args, **kwargs)
        flash('Please enter your billing information.', canon_constants.STATUS_WARNING)
        abort(402)
    return internal


def viper_auth(func):
    """Decorator to test for auth.

    Set session info to g.session, and redirect the user to the log in page
    if they aren't already signed in.

    This decorator will bind the session login to ``g.login``.
    """
    @wraps(func)
    def internal(*args, **kwargs):
        if 'login' in session:
            g.login = session['login']
            return func(*args, **kwargs)
        else:
            return redirect(url_for('sign_in'))
    return internal


def viper_isadmin(func):
    """Decorator to test that the current user session is an admin."""
    @wraps(func)
    def internal(*args, **kwargs):
        try:
            if g.login in config.ADMIN_USERS:
                session['role'] = 'admin'
                return func(*args, **kwargs)
            else:
                flash('User "%s" does not have admin privileges.' % g.login,
                      canon_constants.STATUS_WARNING)
                return redirect(url_for('default'))
        except Exception as ex:
            ex_info = '%s: %s' % (ex.__class__.__name__, ex)
            flash('Problem with admin function: %s' % ex_info,
                  canon_constants.STATUS_ERROR)
            return redirect(url_for('admin'))
    return internal


# TODO: Refactor: This scares me. If we need to limit access to DBs that should be done somewhere else like at the instance level.
def exclude_admin_databases(check_argument):
    """Ensures that users can't perform operations on dbs like admin and config."""
    def decorator(method):
        @wraps(method)
        def check_for_admin_database(*args, **kwargs):
            if check_argument in kwargs:
                if kwargs[check_argument] in Constants.ADMINISTRATIVE_DATABASES:
                    return redirect(url_for('instances'))
            return method(*args, **kwargs)
        return check_for_admin_database
    return decorator


# TODO: Refactor: This can be better accomplished using bson.json_util.
# See api_document in annunciator.py (api_document method should probably moved elsewhere).
def json_stringify(jsondata):
    out = {}
    for k, v in jsondata.iteritems():
        if type(v) is datetime.datetime:
            out[k] = str(v)
        # TODO: Refactor: Bug: Unresolved reference objectid.
        elif type(v) is bson.objectid.ObjectId:
            out[k] = "ObjectId(" + str(v) + ")"
        else:
            out[k] = str(v)
    return out


# TODO: Refactor: Redundant. Should be moved elsewhere if we actually need it.
def json_prettify(s):
    out = {}
    try:
        out = json.dumps(json_stringify(s), sort_keys = False, indent = 2)
    except:
        # TODO: Refactor: Unused reference.
        out = {}
        # TODO make a better handler
    return out


# TODO: Refactor: Needs refactor. Should be moved elsewhere.
def api_url(api_key, function, instance, data=None):
    """ returns json data from OR url fetch """

    if isinstance(data, ImmutableMultiDict):
        data = {key: data.get(key) for key in data.keys()}
    elif isinstance(data, dict):
        data = data
    else:
        data = {}

    data['api_key'] = api_key

    if instance is not None:
        url = "%s/%s/%s" % (config.API_SERVER, function, instance)
    elif function is None:
        url = "%s/" % (config.API_SERVER)
    else:
        if function.startswith('/'):
            function = function[1:]
        url = "%s/%s" % (config.API_SERVER, function)

    out = "{}"

    try:
        f = urllib.urlopen(url, urllib.urlencode(data))
        out = f.read()
        return out

    except Exception as ex:
        app.logger.error("Error retrieving API URL %s: %s" % (url, ex))
        return out


# TODO: Refactor: Needs refactor. Should be moved elsewhere.
def fetch_api_data(api_key, url):
    data = {"api_key": api_key}
    # TODO: Refactor: Shadows api_url.
    api_url = "%s/%s" % (config.API_SERVER, url)

    response_data = "{}"

    try:
        response = urllib.urlopen(api_url, urllib.urlencode(data))
        response_data = response.read()
        return response_data

    except Exception as ex:
        msg = '%s: %s' % (ex.__class__.__name__, str(ex))
        error_id = Utility.obfuscate_exception_message(msg)
        session['error_id'] = error_id
        error_info = {
            'path': request.path,
            'user': getattr(g, 'login', None),
            'api_key': getattr(g, 'api_key', None),
            'context': 'gui fetch_api_data',
        }
        Utility.log_traceback(config, error_id, error_info)
        app.logger.debug("url fetch error:" + str(ex))
        return response_data


# TODO: Refactor: Needs refactor / error checking. Should be moved elsewhere if we actually need it.
def send_email(recipient, subject, body):
    return requests.post(
        "https://api.mailgun.net/v2/objectrocket.mailgun.org/messages",
        auth=("api", "key-9i3dch4p928wedoaj4atoqxoyxb-hy29"),
        data={"from": "ObjectRocket <support@objectrocket.com>",
              "to": recipient,
              "subject": subject,
              "text": body})


# TODO: Refactor: Should be moved out of controllers.
# -----------------------------------------------------------------------
# Configure App Handlers
# -----------------------------------------------------------------------

@app.errorhandler(BillingException)
def stripe_exception_handler(error):
    msg = "Billing Error: {}".format(error)
    flash("There has been an error with your account. Please contact support.", canon_constants.STATUS_ERROR)
    app.logger.error(msg)
    return redirect(url_for('account'))


@app.errorhandler(MongoDBInstanceException)
def mongo_instance_exception_handler(error):
    msg = "Instance Error: {0}".format(error)
    flash("There has been an error with your mongo instance. Please contact support.", canon_constants.STATUS_ERROR)
    app.logger.error(msg)
    return redirect(url_for('default'))


@app.errorhandler(ReplicaException)
def replica_instance_exception_handler(error):
    msg = "Instance Error: {0}".format(error)
    flash("There has been an error with your replica instance. Please contact support.", canon_constants.STATUS_ERROR)
    app.logger.error(msg)
    return redirect(url_for('default'))


@app.errorhandler(500)
def internal_server_error(error):
    """Traps tracebacks for uncaught exceptions."""
    error_id = Utility.obfuscate_exception_message(error)
    error_info = {
        'path': request.path,
        'user': getattr(g, 'login', None),
        'context': 'gui',
    }
    Utility.log_traceback(config, error_id, error_info)
    response = redirect(url_for('error'))
    session['error_id'] = error_id
    app.save_session(session, response)
    return response


@app.errorhandler(402)
def payment_required(error):
    html = billing()
    return html, 402


@app.errorhandler(404)
def page_not_found(error):
    return redirect(url_for('instances'))


@app.context_processor
def inject_constants():
    return {'Constants': Constants}


@app.context_processor
def inject_login():
    login = getattr(g, 'login', None)
    if login is not None:
        return {'login': login}
    return {}


@app.context_processor
def int_function():
    return {'int': int}


@app.before_request
def maintenance_mode():
    #if True:
    if app.config.setdefault('MAINTENANCE', False) and not request.path.startswith('/static'):
        return render_template('maintenance.html')


# TODO: Refactor: Should be moved out of controllers.
# -----------------------------------------------------------------------
# Configure App Filters
# -----------------------------------------------------------------------
@app.template_filter('format_timestamp')
def format_timestamp(ts):
        return Utility.format_timestamp(ts)


# ------------------------
# pass through proxy API calls.  This is done because js only allows local connections, thus make
# local calls through this auth'd proxy
# ------------------------
# Generic call for GUI - more efficient because it avoids an instance lookup
@app.route('/api/<call>/<api_key>', methods=['GET', 'POST'])
@viper_auth
def api_call(call, api_key):
    data = getattr(request, 'form', None)
    return api_url(api_key, call, None, data=data)


@app.route('/api_status', methods=['GET', 'POST'])
@viper_auth
def api_status():
    url = ("%s") % (config.API_SERVER)
    try:
        f = urllib.urlopen(url)
        return f.read()
    except:
        return "{}"


@app.route('/api_collection_stats/<selected_instance>/<database>/<collection>', methods=['GET', 'POST'])
@viper_auth
def api_collection_stats(selected_instance, database, collection):
    url = "/db/%s/collection/%s/stats/get" % (database, collection)

    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    response = fetch_api_data(user_instance.api_key, url)
    response_data = json.loads(response)

    # (Anthony) If an exception takes place in viper_api.controllers then response_data['data']
    # will be a string, not a dict as is expected. Moreover, if a urllib exception takes place
    # in fetch_api_data, then response_data will be an empty dict, causing a KeyError below.
    if not isinstance(response_data.get('data'), dict):
        return redirect(url_for('error'))

    response_data['data']['collection'] = collection
    return json.dumps(response_data)


@app.route('/api_status/<selected_instance>', methods=['GET', 'POST'])
@viper_auth
def api_status_instance(selected_instance):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    return api_url(user_instance.api_key, "status", selected_instance)


@app.route('/api_timeseries/<name>/<selected_instance>')
@viper_auth
def api_timeseries(name, selected_instance):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    if instance is None:
        return ''
    return instance.get_timeseries_data(name)


@app.route('/api_serverStatus/<selected_instance>')
@viper_auth
def api_serverstatus(selected_instance):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if user_instance and user_instance.api_key:
        return api_url(user_instance.api_key, "serverStatus/persecond/get", None)
    else:
        return "{}"


# ----------------------------------------------------------------------------
# Normal urls as part of the app.
# ----------------------------------------------------------------------------
@app.route('/')
@viper_auth
def root():
    """Root url."""
    return redirect(url_for('sign_in'))


@app.route('/error')
def error():
    login = session.get('login', '')
    error_id = session.pop('error_id', '')
    return render_template('500.html', login=login, error_id=error_id, support_email=config.SUPPORT_EMAIL), 500


@app.route('/account')
@viper_auth
def account():
    """Account settings and controls."""
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    if account is None:
        return redirect(url_for('sign_in'))

    return render_template('account/account.html',
                           account=account,
                           email=account.email,
                           login=g.login)


@app.route('/update_account_contact', methods=['POST'])
@viper_auth
def update_account_contact():
    """Update account contact info."""
    company = request.form['company']
    email = request.form['email']
    name = request.form['name']
    phone = request.form['phone']
    zipcode = request.form['zipcode']

    account_manager = AccountManager(config)
    account_manager.update_account_contact(g.login, company=company, email=email, name=name, phone=phone, zipcode=zipcode)

    flash('Account successfully updated.', canon_constants.STATUS_OK)

    return redirect(url_for('account'))


@app.route('/update_password', methods=['POST'])
@viper_auth
def update_password():
    """Update account password."""
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    if account is None or not account.active:
        return redirect(url_for('sign_in'))

    account_manager.update_password(account.login,
                                    request.form[Constants.PASSWORD])

    flash('Password successfully updated.', canon_constants.STATUS_OK)
    return redirect(url_for('account'))


@app.route('/instances/<selected_instance>/stats')
@viper_auth
def instance_stats(selected_instance):
    """Instance statistics page."""
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    instance = account.get_instance_by_name(selected_instance)

    admin = (session.get('role', '') == 'admin')
    stats_enabled = instance.document.get("stats_enabled", False)

    # Temporary feature gate, please remove when the stats gui is released to everyone
    if not stats_enabled and not admin:
        return render_template('instances/instance_stats.html', instance=instance, api_url=config.DEFAULT_API_ENDPOINT)

    return render_template('instances/new_instance_stats.html', instance=instance, api_url=config.DEFAULT_API_ENDPOINT)


@app.route('/instances')
@viper_auth
def instances():
    """"Display account instances."""
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    instances = account.instances
    remote_instances = account.remote_instances

    return render_template('instances/instances.html',
                           account=account,
                           add_instance_enabled=bool(account.stripe_account or account.invoiced),
                           api_keys=account.instance_api_keys,
                           default_mongo_version=config.DEFAULT_MONGO_VERSION,
                           email=account.email,
                           instances=instances,
                           login=g.login,
                           remote_instances=remote_instances,
                           stripe_pub_key=config.STRIPE_PUB_KEY,
                           Utility=Utility)


@app.route('/instances/create', methods=['GET', 'POST'])
@viper_auth
@billing_enabled
def create_instance():
    """Create an instance."""
    form = forms.CreateInstance()

    if request.method == 'GET':
        return render_template('instances/create_instance.html',
                               active_datastores=app.config.get('ACTIVE_DATASTORES'),
                               form=form)

    # TODO(Anthony): See objectrocket/gui#433 (the commented code below needs to be refactored).
    # If form does not validate, send back to create_instance page.
    # if not form.validate_on_submit():
    #     errors = ['{}: {}'.format(key, ' - '.join(val)) for key, val in form.errors.items()]
    #     flash(';'.join(errors), canon_constants.STATUS_ERROR)
    #     return render_template('instances/create_instance.html',
    #                            active_datastores=app.config.get('ACTIVE_DATASTORES'),
    #                            form=form)

    if not csrf.validate_csrf(form.csrf_token.data):
        abort(400)

    # Populate variables from form.
    name = form.name.data
    plan_size_in_gb = form.plan.data
    service_type = form.service_type.data
    version = form.version.data
    zone = form.zone.data
    network = None

    # validate the name of the instance
    # TODO: this should be pushed into a real validation setup
    if re.match(r'^[\w]{2,}$', form.name.data) is None:
        abort(400)

    # TODO: Refactor: move pretty much all of the following logic into core.
    # Determine the type of instance to use for mongodb.
    if service_type == Constants.MONGODB_SERVICE:
        if plan_size_in_gb == 1:
            instance_type = Constants.MONGODB_REPLICA_SET_INSTANCE
        else:
            instance_type = Constants.MONGODB_SHARDED_INSTANCE

    # Determine the type of instance to use for tokumx.
    elif service_type == Constants.TOKUMX_SERVICE:
        if plan_size_in_gb == 1:
            instance_type = Constants.TOKUMX_REPLICA_SET_INSTANCE
        else:
            instance_type = Constants.TOKUMX_SHARDED_INSTANCE

    # Determine the type of instance to use for redis.
    elif service_type == Constants.REDIS_SERVICE:
        network = form.network.data
        instance_type = Constants.REDIS_HA_INSTANCE

    account = AccountManager(config).get_account(g.login)
    instance_manager = InstanceManager(config)

    # Check if an instance with the same name already belongs to the account.
    if instance_manager.instance_exists(g.login, name):
        flash_message = "Cannot create instance '%s': an instance with this name already exists." % name
        flash(flash_message, canon_constants.STATUS_ERROR)
        return redirect(url_for('instances'))

    # Check if there are any free instances meeting the given specifications.
    if not instance_manager.free_instance_count(plan_size_in_gb, zone, version, service_type, instance_type, network):
        flash_message = ("Cannot create instance '%s': no instances are available for plan %s, zone %s, version %s."
                         % (name, plan_size_in_gb, zone, version))
        flash(flash_message, canon_constants.STATUS_ERROR)

        subject = "Instance not available in UI."
        body = ("Login %s attempted to add %s instance type %s with plan: %s zone: %s name: %s, version: %s, network: %s"
                % (g.login, service_type, instance_type, plan_size_in_gb, zone, name, version, network))
        send_email(config.SUPPORT_EMAIL, subject, body)
        return redirect(url_for('instances'))

    # Check if at or above max instances for this account.
    if len(account.instances) >= config.MAX_INSTANCES_PER_USER:
        flash_message = "Please contact support if you need more than %d instances"
        flash(flash_message % config.MAX_INSTANCES_PER_USER, canon_constants.STATUS_WARNING)
        return redirect(url_for('instances'))

    # Attempt to add a new instance of the given specifications.
    try:
        account.add_instance(name, zone, plan_size_in_gb, version, service_type, instance_type, network)
        Utility.log_to_db(config, 'Created instance.', {'login': g.login, 'area': 'gui', 'instance_name': name})
        flash('Instance "{}" successfully added to account.'.format(name), canon_constants.STATUS_OK)
        return redirect(url_for('instances'))
    except Exception as ex:
        exception_uuid = Utility.obfuscate_exception_message(ex.message)
        flash_message = ("There was a problem creating an instance. If this problem persists, contact"
                         "support and provide Error ID %s." % (exception_uuid))
        flash(flash_message, canon_constants.STATUS_ERROR)

        log_message = "Failed to create instance for login %s, plan %s, zone %s, name %s: %s" % (g.login, plan_size_in_gb, zone, name, ex)
        app.logger.error(log_message)
        return redirect(url_for('instances'))


@app.route('/<instance_name>/delete', methods=['POST'])
@viper_auth
def delete_instance(instance_name):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, instance_name)
    instance_manager.recycle_instance(instance.id)
    return redirect(url_for('instances'))


@app.route('/instances/<selected_instance>/shards')
@viper_auth
def shards(selected_instance):
    """Instance shards or replica set."""
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    if instance is None:
        abort(404)

    html = ''
    if instance.type in (Constants.MONGODB_SHARDED_INSTANCE, Constants.TOKUMX_SHARDED_INSTANCE):
        aggregate_stats = instance.shard_balance
        html = render_template(template_name_or_list='instances/{}/_shard_info.html'.format(instance.service),
                               aggregate_stats=aggregate_stats,
                               instance=instance)

    elif instance.type in (Constants.MONGODB_REPLICA_SET_INSTANCE, Constants.TOKUMX_REPLICA_SET_INSTANCE):
        if instance.replica_set.primary:
            primary = instance.replica_set.primary
            has_primary = True
        else:
            primary = instance.replica_set.members[0]
            has_primary = False

        html = render_template('instances/_replica_set_info.html',
                               get_host_zone=Utility.get_host_zone,
                               has_primary=has_primary,
                               instance=instance,
                               primary=primary)

    return html


@app.route('/instances/<selected_instance>')
@viper_auth
def instance_details(selected_instance):
    """Instance details page."""
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if user_instance is None:
        abort(404)

    account_monitor = monitor.AccountMonitor(config)
    account_monitoring_checks = account_monitor.get_enabled_checks(asset_type=monitor.INSTANCE_ASSET_TYPE,
                                                                   user_controllable_only=True)

    try:
        enable_copy_database = user_instance.instance_connection.server_info()['versionArray'] >= [2, 4, 0, 0]
    except Exception:
        enable_copy_database = False

    balancer = None
    if user_instance.type in (Constants.MONGODB_SHARDED_INSTANCE, Constants.TOKUMX_SHARDED_INSTANCE):
        balancer = user_instance.balancer

    # Get instance operation states
    database_compaction_state = user_instance.compression.get(Constants.COMPACTION_STATE, None)

    database_copy_state = None
    copy_database_document = user_instance.document.get('copy_database', None)
    if copy_database_document:
        database_copy_state = copy_database_document.get('state', None)

    database_repair_state = False
    if user_instance.type in (Constants.MONGODB_REPLICA_SET_INSTANCE, Constants.TOKUMX_REPLICA_SET_INSTANCE):
        database_repair_state = user_instance.repair_state

    return render_template('instances/{}/instance_details.html'.format(user_instance.service),
                           account_monitoring_checks=account_monitoring_checks,
                           balancer=balancer,
                           database_compaction_state=database_compaction_state,
                           database_copy_state=database_copy_state,
                           database_repair_state=database_repair_state,
                           enable_copy_database=enable_copy_database,
                           get_host_zone=Utility.get_host_zone,
                           instance=user_instance,
                           is_sharded_instance=user_instance.type in (Constants.MONGODB_SHARDED_INSTANCE, Constants.TOKUMX_SHARDED_INSTANCE),
                           max_databases_per_replica_set_instances=config.MAX_DATABASES_PER_REPLICA_SET_INSTANCE)


@app.route('/instances/<selected_instance>/space_usage')
@viper_auth
def instance_space_usage(selected_instance):
    """Calculate instance usage totals and percentages."""
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if instance is None:
        abort(404)

    usage_totals = instance.space_usage

    return render_template(template_name_or_list='instances/{}/_space_usage.html'.format(instance.service),
                           instance=instance,
                           usage_totals=usage_totals)


@app.route('/rename_instance', methods=['POST'])
@viper_auth
def rename_instance():
    current_name = request.form['current_name']
    new_name = request.form['new_name']
    instance_manager = InstanceManager(config)
    app.logger.debug("renaming %s to %s:" % (current_name, new_name))

    if not current_name:
        message = "Cannot rename an empty instance name"
        app.logger.error(message)
        return redirect(url_for('instance_details', selected_instance=current_name))

    if not new_name:
        message = "Cannot rename instance %s: A non-empty new instance name is required." % (current_name)
        flash(message, canon_constants.STATUS_ERROR)
        return redirect(url_for('instance_details', selected_instance=current_name))

    if instance_manager.instance_exists(g.login, new_name):
        message = "Cannot rename instance %s to %s: An instance named %s already exists." % (current_name, new_name, new_name)
        flash(message, canon_constants.STATUS_ERROR)
        return redirect(url_for('instance_details', selected_instance=current_name))

    instance_manager.rename_instance(g.login, current_name, new_name)
    flash('Instance successfully renamed.', canon_constants.STATUS_OK)

    ref = urlparse(request.referrer)
    if ref.path == '/instances':
        return redirect(url_for('instances'))
    else:
        return redirect(url_for('instance_details', selected_instance=new_name))


@app.route('/instances/<selected_instance>/cluster')
@viper_auth
def cluster(selected_instance):
    """Display sharded cluster details."""
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if not instance:
        abort(404)
    elif instance.type not in (Constants.MONGODB_SHARDED_INSTANCE, Constants.TOKUMX_SHARDED_INSTANCE):
        return redirect(url_for('instance_details', selected_instance=selected_instance))

    return render_template('instances/{}/cluster.html'.format(instance.service), instance=instance, get_host_zone=Utility.get_host_zone)


@app.route('/add_instance_user/<selected_instance>', methods=['POST'])
@viper_auth
def add_instance_user(selected_instance):
    """Adds a user to each database in this instance"""
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    user = request.form['username']
    password = request.form['password']
    read_only = request.form.get('read_only', 'off') == 'on'

    for database in instance.databases:
        try:
            instance.add_user(database.name, user, password, read_only)
        except Exception as ex:
            exception_uuid = Utility.obfuscate_exception_message(ex.message)
            flash_message = ("There was a problem updating user information for instance %s. If "
                             "this problem persists, contact "
                             "<a mailto:%s>%s</a> and provide Error ID %s.")

            flash_message = flash_message % (instance.name, config.SUPPORT_EMAIL, config.SUPPORT_EMAIL, exception_uuid)

            error_info = {
                'path': request.path,
                'user': getattr(g, 'login', None),
                'context': 'gui'
            }
            Utility.log_traceback(config, exception_uuid, error_info)
            flash(flash_message, Constants.FLASH_ERROR)

    return redirect(url_for('instance_details', selected_instance=selected_instance))


# TODO(Anthony): This route should be broken into two routes. One for DB creation,
# and one for user creation.
@app.route('/create_instance_user/<selected_instance>', methods=['POST'])
@app.route('/create_instance_user/<selected_instance>/<selected_database>', methods=['POST'])
@exclude_admin_databases(check_argument='selected_database')
@viper_auth
def create_instance_user(selected_instance, selected_database=None):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if user_instance:
        try:
            if not selected_database:
                selected_database = request.form['database']

            user = request.form['username']
            password = request.form['password']
            read_only = request.form.get('read_only', 'off') == 'on'

            if user_instance.has_database(selected_database):
                # The database exists, just add a user to it.
                user_instance.add_user(selected_database, user, password, read_only)

                # Redirect to database because that's where this request came from.
                # See refactor note above.
                return redirect(url_for('database', selected_instance=selected_instance, selected_database=selected_database))
            else:
                # The database does not exist, add it and the user.
                user_instance.add_database(selected_database, user, password)

        except Exception as ex:

            flash_message = None

            if hasattr(ex, 'code'):
                if ex.code == Constants.MAX_DATABASES_REACHED:
                    flash_message = "Error adding database: This instance's plan is limited to a single database."
                elif ex.code == Constants.NO_USERS_FOR_EMPTY_DBS:
                    flash_message = "Error adding user: You may not add users to empty databases without users."

            if flash_message is None:
                exception_uuid = Utility.obfuscate_exception_message(ex.message)
                flash_message = ("There was a problem with your request. If "
                                 "this problem persists, contact support and provide Error ID %s.")

                flash_message = flash_message % (exception_uuid)

                error_info = {
                    'path': request.path,
                    'user': getattr(g, 'login', None),
                    'context': 'gui',
                }

                Utility.log_traceback(config, exception_uuid, error_info)

            flash(flash_message, canon_constants.STATUS_ERROR)

        return redirect(url_for('instance_details', selected_instance=selected_instance))


@app.route('/delete_instance_user/<selected_instance>/<selected_database>', methods=['POST'])
@app.route('/delete_instance_user/<selected_instance>/<selected_database>/<username>', methods=['POST'])
@exclude_admin_databases(check_argument='selected_database')
@viper_auth
def delete_instance_user(selected_instance, selected_database, username=None):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if username is None:
        username = request.form['username']

    database = user_instance.get_database(selected_database)

    if user_instance.type in (Constants.MONGODB_REPLICA_SET_INSTANCE, Constants.TOKUMX_REPLICA_SET_INSTANCE) and len(database.users) <= 1:
        flash('Cannot remove the last user of a replicated instance. Please add another user first.',
              canon_constants.STATUS_ERROR)

    user_instance.delete_user(selected_database, username)

    return redirect(url_for('database', selected_instance=selected_instance, selected_database=selected_database))


@app.route('/drop_database', methods=['POST'])
@viper_auth
def drop_database():
    selected_database = request.form['db']
    selected_instance = request.form['instance']

    if selected_database in Constants.ADMINISTRATIVE_DATABASES:
        flash("Administrative databases cannot be dropped.", canon_constants.STATUS_WARNING)

    # Verify this db actually belongs to this account.
    database_found = False

    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    for database in instance.databases:
        if database.name == selected_database:
            database_found = True

    if database_found:
        try:
            instance.instance_connection.drop_database(selected_database)
            flash("Database %s dropped." % selected_database, canon_constants.STATUS_OK)
        except Exception as ex:
            exception_message = "Failed to drop database %s for account %s, instance %s: %s" % (selected_database, g.login, instance.name, ex)
            exception_uuid = Utility.obfuscate_exception_message(exception_message)
            flash_message = ("A problem occurred while dropping database %s. If the problem persists, please contact"
                             "support and provide Error ID %s." % (selected_database, exception_uuid))
            flash(flash_message, canon_constants.STATUS_ERROR)
    else:
        flash("Error dropping database %s: database not found." % selected_database, canon_constants.STATUS_ERROR)

    return redirect(url_for('instance_details', selected_instance=selected_instance))


@app.route('/copy_database/<selected_instance>', methods=['GET', 'POST'])
@viper_auth
def copy_database(selected_instance):
    """Copy database."""
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if user_instance:
        try:
            connect_string = request.form['connect_string']
            database = request.form['database']
            username = request.form['username']
            password = request.form['password']

            # The database exists, just add a user to it
            user_instance.copy_database(database, database, connect_string, username, password)
            flash('Database copy has been scheduled.', canon_constants.STATUS_OK)
        except Exception as ex:
            flash_message = "Error copying database: %s" % ex
            flash(flash_message, canon_constants.STATUS_ERROR)

    return redirect(url_for('instance_details',
                            selected_instance=selected_instance))


@app.route('/instances/<selected_instance>/databases')
@viper_auth
def databases(selected_instance):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    if instance is None:
        abort(404)

    databases = instance.databases
    html = render_template(template_name_or_list='instances/{}/_databases.html'.format(instance.service),
                           databases=databases,
                           instance=instance)
    return html


@app.route('/instances/<selected_instance>/databases/<selected_database>', methods=['GET', 'POST'])
@exclude_admin_databases(check_argument='selected_database')
@viper_auth
def database(selected_instance, selected_database):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if not user_instance or user_instance == Constants.REDIS_SERVICE:
        abort(404)

    user_database = user_instance.get_database(selected_database)

    is_sharded_instance = user_instance.type in (Constants.MONGODB_SHARDED_INSTANCE, Constants.TOKUMX_SHARDED_INSTANCE)
    default_autohash_on_id = is_sharded_instance and user_instance.plan < config.DEFAULT_AUTO_HASH_ON_ID_CUTOFF_IN_GB

    return render_template('instances/instance_database.html',
                           collections=user_database.get_collection_list(),
                           database=user_database,
                           default_autohash_on_id=default_autohash_on_id,
                           has_more_collections=len(user_database.collection_list),
                           instance=user_instance,
                           is_sharded_instance=is_sharded_instance,
                           login=g.login,
                           users=user_database.users)


@app.route('/instances/<selected_instance>/databases/<selected_database>/collections/<selected_collection>', methods=['GET', 'POST'])
@exclude_admin_databases(check_argument='selected_database')
@viper_auth
def collection(selected_instance, selected_database, selected_collection):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if not user_instance or user_instance.service == Constants.REDIS_SERVICE:
        abort(404)

    user_database = user_instance.get_database(selected_database)
    user_collection = user_database.get_collection(selected_collection)
    indexes = user_database.get_indexes(user_collection)
    shard_keys = user_database.get_shard_keys(user_collection)

    if user_instance.type in (Constants.MONGODB_SHARDED_INSTANCE, Constants.TOKUMX_SHARDED_INSTANCE):
        chunks = user_instance.get_chunks(user_collection)
    else:
        chunks = []

    try:
        sample_document = json_prettify(user_database.get_sample_document(selected_collection))
    except ValueError:
        sample_document = None

    return render_template('instances/{}/collection.html'.format(user_instance.service),
                           chunks=chunks,
                           collection=user_collection,
                           database=user_database,
                           indexes=indexes,
                           instance=user_instance,
                           login=g.login,
                           sample_document=sample_document,
                           shard_keys=shard_keys)


@app.route('/instances/<selected_instance>/databases/<selected_database>/get_collections')
@viper_auth
def get_collection_page(selected_instance, selected_database):
    """Gets a JSON object containing a single page of collections."""
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if not user_instance:
        abort(404)

    limit = int(request.args.get('limit', 25))
    page_number = int(request.args.get('page_number', 0))

    user_database = user_instance.get_database(selected_database)
    user_collections = list(user_database.get_collection_list(limit=limit, page_number=page_number))

    for i, collection in enumerate(user_collections):
        collection_dict = {
            'name': collection.name,
            'document_count': collection.document_count or 0,
            'size': filesizeformat(collection.size or 0, binary=True),
            'average_object_size_in_bytes': filesizeformat(collection.average_object_size_in_bytes or 0, binary=True),
            'total_index_size_in_bytes': filesizeformat(collection.total_index_size_in_bytes or 0, binary=True),
            'sharded': 'True' if collection.sharded else 'False'
        }
        user_collections[i] = collection_dict

    return json.dumps({'collections': user_collections}), 200, {'content-type': 'application/json'}


@app.route('/instances/<selected_instance>/databases/<selected_database>/create_collection')
@viper_auth
def add_collection(selected_instance, selected_database):
    """Add new collection."""
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    user_database = user_instance.get_database(selected_database)

    return render_template('instances/collection_create.html',
                           instance=user_instance,
                           is_sharded_instance=user_instance.type in (Constants.MONGODB_SHARDED_INSTANCE, Constants.TOKUMX_SHARDED_INSTANCE),
                           database=user_database,
                           default_mongo_version=config.DEFAULT_MONGO_VERSION)


@app.route('/instances/<selected_instance>/databases/<selected_database>/collections/<selected_collection>/create_index', methods=['GET', 'POST'])
@viper_auth
def add_index(selected_instance, selected_database, selected_collection):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    user_database = user_instance.get_database(selected_database)
    user_collection = user_database.get_collection(selected_collection)

    if request.method == 'GET':
        # Add new index.
        return render_template('instances/collection_index_create.html',
                               instance=user_instance,
                               database=user_database,
                               collection=user_collection)
    else:
        background = request.form.get('background', False)
        drop_dups = request.form.get('dropdups', False)
        index_name = request.form.get('name', '')
        unique = request.form.get('unique', False)

        # TokuMX does not allow creation of unique indexes in the background.
        if user_instance.service == Constants.TOKUMX_SERVICE:
            if unique and background:
                flash('Cannot build a unique index in the background for TokuMX instances.', canon_constants.STATUS_WARNING)
                return redirect(url_for('add_index', selected_instance=selected_instance, selected_database=selected_database, selected_collection=selected_collection))

        all_index_keys = request.form['all_index_keys']
        index_keys = json.loads(all_index_keys, object_pairs_hook=collections.OrderedDict)

        try:
            user_database.add_index(selected_collection,
                                    index_keys,
                                    background=background,
                                    dropdups=drop_dups,
                                    index_name=index_name,
                                    unique=unique)
        except Exception as ex:
            exception_uuid = Utility.obfuscate_exception_message(ex.message)
            flash_message = ("There was a problem creating this index. If this problem persists, contact "
                             "support and provide Error ID %s." % (exception_uuid))
            Utility.log_traceback(config=config, error_id=exception_uuid)
            flash(flash_message, canon_constants.STATUS_ERROR)

        return redirect(url_for('collection', selected_instance=selected_instance, selected_database=selected_database,
                                selected_collection=selected_collection))


@app.route('/create_collection/<selected_instance>/<selected_database>', methods=['POST'])
@exclude_admin_databases(check_argument='selected_database')
@viper_auth
def create_collection(selected_instance, selected_database):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    user_database = user_instance.get_database(selected_database)

    try:
        if 'all_shard_keys' in request.form:
            all_shard_keys = request.form['all_shard_keys']
            shard_keys = json.loads(all_shard_keys, object_pairs_hook=collections.OrderedDict)
            user_database.shard_collection(request.form['collection'], shard_keys=shard_keys)
        else:
            user_database.add_collection(request.form['collection'])
    except Exception as ex:
        exception_uuid = Utility.obfuscate_exception_message(ex.message)
        Utility.log_traceback(config, exception_uuid)
        app.logger.error(ex)
        flash_message = ("There was a problem creating this collection. If this problem persists, contact "
                         "support and provide Error ID %s." % (exception_uuid))
        flash(flash_message, canon_constants.STATUS_ERROR)

    return redirect(url_for('database', selected_instance=selected_instance, selected_database=selected_database))


@app.route('/shard_collection/<selected_instance>/<selected_db>/<selected_collection>', methods=['POST'])
@exclude_admin_databases(check_argument='selected_db')
@viper_auth
def shard_collection(selected_instance, selected_db, selected_collection):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    user_database = user_instance.get_database(selected_db)

    all_shard_keys = request.form['all_shard_keys']
    shard_keys = json.loads(all_shard_keys, object_pairs_hook=collections.OrderedDict)
    app.logger.debug("shard keys are " + repr(shard_keys))

    create_indexes = request.form.get('create_indexes', False)

    try:
        user_database.shard_collection(selected_collection, shard_keys=shard_keys, create_indexes=create_indexes)
    except Exception as ex:
        exception_uuid = Utility.obfuscate_exception_message(ex.message)
        flash_message = ("There was a problem applying this shard key. If this problem persists, contact"
                         " support and provide Error ID %s." % (exception_uuid))
        flash(flash_message, canon_constants.STATUS_ERROR)

    return redirect(url_for('collection', selected_instance=selected_instance, selected_database=selected_db,
                            selected_collection=selected_collection))


@app.route('/notifications')
@viper_auth
def notifications():
    """Display account notification messages."""
    message_manager = MessageManager(config)
    messages = message_manager.get_messages(g.login)
    annunciator = Annunciator(config)
    alarms = annunciator.get_alarms_for_login(g.login)
    alarms = [alarm for alarm in alarms if not (alarm.state == Alarm.CLEARED or alarm.support_only)]
    return render_template('notifications/notifications.html',
                           alarms=alarms,
                           login=g.login,
                           messages=messages)


@app.route('/clear_alarm', methods=['POST'])
@viper_auth
def clear_alarm():
    """Clears alarms."""
    alarm_id = request.form['alarm_id']
    annunciator = Annunciator(config)
    alarm = annunciator.get_alarm(alarm_id)

    if alarm.login == g.login:
        annunciator.mark_alarm_as_cleared(alarm.id)
        flash('Alarm cleared.', canon_constants.STATUS_OK)

    return redirect(url_for('notifications'))


@app.route('/clear_all_alarms/<selected_instance>', methods=['POST'])
@viper_auth
def clear_all_alarms(selected_instance):
    """Clear all alarms for a given instance."""
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    annunciator = Annunciator(config)
    alarms = annunciator.get_alarms_for_login(g.login)
    alarms = [alarm for alarm in alarms if not (alarm.state == Alarm.CLEARED or alarm.support_only) and alarm.asset_id == instance.name]

    for alarm in alarms:
        response = api_call('/alarm/clear/{}'.format(alarm['id']), instance.api_key)
        data = json.loads(response)

        if data.get('rc', 1) != 0:
            msg = 'Unable to clear all alarms. If this problem persists, contact <a href="mailto:{0}">{0}</a>'.format(config.SUPPORT_EMAIL)
            flash(msg, Constants.FLASH_ERROR)
            break

    return redirect(url_for('notifications'))


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    session.pop('login', None)
    serializer = itsdangerous.URLSafeTimedSerializer(app.signing_key)
    account_manager = AccountManager(config)

    if request.method == 'POST':
        #  The user is requesting a reset token (Step 1).
        if Constants.LOGIN in request.form:
            login = request.form[Constants.LOGIN]
            account = account_manager.get_account(login)

            if account is not None and account.active:
                # Generate reset token.
                pr_host = config.PASSWORD_RESET_HOST
                pr_token = serializer.dumps(login)
                pr_link = ('%s/reset_password?token=%s'
                           % (pr_host, pr_token))

                subject = 'ObjectRocket Password Reset Request'
                body = (Constants.RESET_PASSWORD_TEMPLATE
                        % (login, pr_link))

                # Email to user.
                send_email(account.email, subject, body)
                app.logger.info('Password reset email sent to login %s'
                                % login)
                return render_template('sign_in/reset_email_sent.html')

            elif account is not None:
                # Account is deactivated.
                flash('The specified account is currently deactivated. Contact support to reactivate.',
                      canon_constants.STATUS_WARNING)
                return redirect(url_for('sign_in'))

            else:
                # Account does not exist.
                flash('The specified account does not exist.', canon_constants.STATUS_ERROR)
                return redirect(url_for('sign_in'))

        # User's token is valid, changing password (Step 3).
        if 'confirmPassword' in request.form:
            token = request.form['token']

            # Ensure token is still valid.
            try:
                max_age = Constants.PASSWORD_RESET_TOKEN_TTL_IN_SECONDS
                login = serializer.loads(token, max_age=max_age)
                password = request.form[Constants.PASSWORD]

                account_manager.update_password(login, password)
                flash('Password successfully reset. Please login.', canon_constants.STATUS_OK)
                return redirect(url_for('sign_in'))

            except itsdangerous.BadSignature:
                app.logger.info('Bad password reset token presented: %s'
                                % token)
                flash("Your password reset token was invalid. Try again.", canon_constants.STATUS_ERROR)
                return redirect(url_for('sign_in'))

    # The user has a token and wants to validate it (Step 2).
    if request.method == 'GET':
        token = request.args.get('token')
        if token:
            try:
                max_age = Constants.PASSWORD_RESET_TOKEN_TTL_IN_SECONDS
                serializer.loads(token, max_age=max_age)
                return render_template('sign_in/change_password.html',
                                       token=token)

            except itsdangerous.BadSignature:
                app.logger.info('Bad password reset token presented: %s'
                                % token)
                flash('Your password reset token was invalid. Try again.', canon_constants.STATUS_ERROR)
                return redirect(url_for('sign_in'))

        else:
            flash('Your password reset token was invalid. Try again.', canon_constants.STATUS_ERROR)
            return redirect(url_for('sign_in'))


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    """User sign in route."""
    # Clear any previous session info.
    session.clear()

    # Handle GET request.
    if request.method == 'GET':
        return _render_sign_in()

    login = request.form['login']
    password = request.form['password']

    account_manager = AccountManager(config)
    if not account_manager.authenticated(login, password):
        flash('Sign in failed.', canon_constants.STATUS_ERROR)
        return _render_sign_in(401)

    session['login'] = login

    account = account_manager.get_account(login)
    if not account.accepted_msa:
        return redirect(url_for('msa'))

    return redirect(url_for('instances'))


def _render_sign_in(code=200):
    context = {}
    if app.config['CONFIG_MODE'] != 'production':  # Will enable in prod when ready.
        from viper.ext import sso
        context.update({
            'authn_request': sso.util.create_encoded_saml_request(),
            'relay_state': sso.util.create_encoded_relay_state(),
            'sso_idp_url': sso.config.SSO_IDP_URL
        })

    return render_template('sign_in/sign_in.html', **context), code


@app.route('/logout', methods=['POST'])
def logout():
    """Log out user."""
    session.clear()
    return redirect(url_for('sign_in'))


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    """The signup form."""
    # Don't want any random person to just sign up for a QA account.
    if app.config['CONFIG_MODE'] == 'qa':
        flash('Please contact ObjectRocket support if you need a QA account.', canon_constants.STATUS_WARNING)
        return redirect(url_for('sign_in'))

    if request.method == 'POST':
        account_manager = AccountManager(config)

        # TODO: Put a unique constraint on user names to fix
        #       this race condition

        if account_manager.get_account(request.form['email']):
            flash('The email "{}" is already associated with an account.'.format(request.form['email']), canon_constants.STATUS_ERROR)

        else:
            account = account_manager.create_account(login=request.form['email'],
                                                     password=request.form['password'],
                                                     email=request.form['email'],
                                                     name=request.form['name'],
                                                     company=request.form.get('company'),
                                                     phone=request.form.get('phone'),
                                                     zipcode=None)
            annunciator = Annunciator(config)
            annunciator.create_alarm(Constants.ACCOUNT_SIGNUP,
                                     account.login,
                                     Alarm.INFO,
                                     account.login,
                                     notify_once=True,
                                     supplemental_data=account.login)
            send_signup_to_salesforce.delay(account.name, account.email, account.phone, account.login)
            session['login'] = account.login
            return redirect(url_for('sign_up_thanks'))

    return render_template('sign_up/sign_up.html')

@app.route('/thanks', methods=['GET', 'POST'])
def sign_up_thanks():
    """The signup thank you page"""
    return render_template('sign_up/sign_up_thanks.html')


@app.route('/msa')
@viper_auth
def msa():
    return render_template('sign_up/msa.html')


@app.route('/msa_agree')
@viper_auth
def msa_agree():
    # Record agreement, then redirect to home.
    account_manager = AccountManager(config)
    account_manager.accept_msa(g.login)
    return redirect(url_for('instances'))


@app.route('/msa_disagree')
@viper_auth
def msa_disagree():
    return render_template('sign_up/msa_disagree.html')


@app.route('/billing')
@viper_auth
def billing():
    billing_manager = BillingManager(config)
    invoices = collections.OrderedDict()
    manually_invoiced = False
    subscription = {}
    date_format = "%B %d, %Y"

    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)

    if account.invoiced:
        manually_invoiced = True
        billing_manager = BillingManager(config)
        plan_definition = billing_manager.get_plan_definition(g.login, billable_only=False)

        if plan_definition:
            (plan_id, plan_name) = billing_manager.get_plan_id_and_name(plan_definition)
            subscription['name'] = plan_name + " (Custom)"
        else:
            subscription['name'] = "Custom Plan"

        if account.invoiced_amount and account.invoiced_currency:
            invoice_amount_in_dollars = float(account.invoiced_amount) / 100
            subscription['amount'] = ('$%.2f' % invoice_amount_in_dollars) + " " + account.invoiced_currency.upper()
        else:
            subscription['amount'] = "(Amount defined by contract)"

    else:
        stripe_subscription = billing_manager.get_user_stripe_subscription(g.login)

        if stripe_subscription:
            plan = stripe_subscription['plan']
            subscription['name'] = plan['name']

            plan_cost_in_dollars = float(plan['amount']) / 100
            subscription['amount'] = ('$%.2f' % plan_cost_in_dollars) + " " + plan['currency'].upper()

            start_timestamp = datetime.datetime.fromtimestamp(stripe_subscription['start'])
            subscription['start_date'] = start_timestamp.strftime(date_format)

            next_bill_timestamp = datetime.datetime.fromtimestamp(stripe_subscription['current_period_end'])
            subscription['next_bill_date'] = next_bill_timestamp.strftime(date_format)

    stripe_invoices = billing_manager.get_account_invoices(g.login)

    if stripe_invoices:
        for invoice_datum in stripe_invoices['data']:
            invoice = {}

            invoice_timestamp = datetime.datetime.fromtimestamp(invoice_datum['date'])
            invoice['date'] = invoice_timestamp.strftime(date_format)

            if invoice_datum['lines']['subscriptions']:
                invoice_subscription = invoice_datum['lines']['subscriptions'][0]

                invoice_subscription_start_timestamp = datetime.datetime.fromtimestamp(invoice_subscription['period']['start'])
                invoice['start_date'] = invoice_subscription_start_timestamp.strftime(date_format)

                invoice_subscription_end_timestamp = datetime.datetime.fromtimestamp(invoice_subscription['period']['end'])
                invoice['end_date'] = invoice_subscription_end_timestamp.strftime(date_format)

            else:
                invoice_start_timestamp = datetime.datetime.fromtimestamp(invoice_datum['period_start'])
                invoice['start_date'] = invoice_start_timestamp.strftime(date_format)

                invoice_end_timestamp = datetime.datetime.fromtimestamp(invoice_datum['period_end'])
                invoice['end_date'] = invoice_end_timestamp.strftime(date_format)

            invoice_amount_in_dollars = float(invoice_datum['total']) / 100
            invoice['amount'] = ('$%.2f' % invoice_amount_in_dollars) + " " + invoice_datum['currency'].upper()

            if invoice_datum['paid']:
                invoice['status'] = 'Paid in Full'
            else:
                invoice['status'] = 'Due Immediately'

            invoices[invoice_datum['id']] = invoice

    active_card = billing_manager.get_account_active_card(g.login)
    if active_card is not None:
        active_card['exp'] = '{0.exp_month} / {0.exp_year}'.format(active_card)
        active_card['last4'] = u'{0}{0}{0}{0} {0}{0}{0}{0} {0}{0}{0}{0} {1.last4}'.format(u'\u2022', active_card)

    return render_template('billing/billing.html',
                           active_card=active_card,
                           subscription=subscription,
                           manually_invoiced=manually_invoiced,
                           login=g.login,
                           invoices=invoices,
                           stripe_pub_key=config.STRIPE_PUB_KEY)


@app.route('/set_credit_card', methods=['POST'])
@viper_auth
def set_credit_card():
    billing_manager = BillingManager(config)
    valid_redirect_routes = [url_for('billing'), url_for('instances')]

    try:
        billing_manager.set_credit_card(g.login, request.form['stripe_token'])
        flash('Credit card information updated.', canon_constants.STATUS_OK)

    except stripe.CardError as ex:
        flash(ex.message, canon_constants.STATUS_ERROR)

    return_target = request.form.get('returntarget', url_for('billing'))
    if return_target in valid_redirect_routes:
        return redirect(return_target)
    else:
        return redirect(url_for('billing'))


@app.route('/invoices/<invoice_id>')
@viper_auth
def show_invoice(invoice_id):
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)

    billing_manager = BillingManager(config)
    invoice = billing_manager.get_invoice(g.login, invoice_id)

    return render_template('billing/invoice.html',
                           account=account,
                           invoice=invoice,
                           format_timestamp=Utility.format_timestamp)


@app.route('/external')
@viper_auth
def external():
    return redirect(url_for('new_relic'))


@app.route('/external/new_relic')
@viper_auth
def new_relic():
    def obfuscate(str):
        return '{}{}'.format('*' * (len(str) - 4), str[-4:])

    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)

    obfuscated_new_relic_key = None

    if account.new_relic_key:
        obfuscated_new_relic_key = obfuscate(account.new_relic_key)

    return render_template('external/new_relic.html',
                           obfuscated_new_relic_key=obfuscated_new_relic_key,
                           login=g.login)


@app.route('/external/add_new_relic_key', methods=['POST'])
@viper_auth
def add_new_relic_key():
    """Update account contact info route."""
    try:
        new_relic_key = request.form['license_key']
        account_manager = AccountManager(config)
        account_manager.add_new_relic_key(g.login, new_relic_key, enable_on_all_instances=True)
        flash('Your New Relic license key was successfully updated. If your information does not appear on the New'
              ' Relic site within 30 minutes, please contact support.', canon_constants.STATUS_OK)

    except Exception as ex:
        exception_uuid = Utility.obfuscate_exception_message(ex.message)
        flash_message = ("There was a problem with your New Relic license key. If this problem persists and you "
                         "believe your key is valid, please contact support and provide Error ID {}.".format(
                         exception_uuid))
        flash(flash_message, canon_constants.STATUS_ERROR)

    return redirect(url_for('new_relic'))


@app.route('/external/delete_new_relic_key', methods=['POST'])
@viper_auth
def delete_new_relic_key():
    """Update account contact info route."""
    try:
        account_manager = AccountManager(config)
        account_manager.delete_new_relic_key(g.login)
        flash('Your New Relic license key was successfully deleted.', canon_constants.STATUS_OK)

    except Exception as ex:
        exception_uuid = Utility.obfuscate_exception_message(ex.message)
        flash_message = ("There was a problem with deleting your license key. If this problem persists, please contact "
                         "support and provide Error ID {}.".format(exception_uuid))
        flash(flash_message, canon_constants.STATUS_ERROR)

    return redirect(url_for('new_relic'))


@app.route('/external/amazon')
@viper_auth
def amazon():
    def obfuscate(str):
        return '{}{}'.format('*' * (len(str) - 4), str[-4:])

    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)

    obfuscated_ec2_access_key = None
    obfuscated_ec2_secret_key = None

    if account.aws_access_key_id:
        obfuscated_ec2_access_key = obfuscate(account.aws_access_key_id)
        obfuscated_ec2_secret_key = obfuscate(account.aws_secret_access_key)

    return render_template('external/amazon.html',
                           obfuscated_ec2_access_key=obfuscated_ec2_access_key,
                           obfuscated_ec2_secret_key=obfuscated_ec2_secret_key,
                           login=g.login)


@app.route('/external/add_ec2_settings', methods=['POST'])
@viper_auth
def add_ec2_settings():
    """Add EC2 settings route."""

    ec2_region = request.form.get('ec2_region')
    ec2_security_group = request.form.get('ec2_security_group', None)
    ec2_access_key = request.form.get('ec2_access_key')
    ec2_secret_key = request.form.get('ec2_secret_key')
    aws_manager = AWSManager(config, ec2_region, ec2_access_key, ec2_secret_key)

    error = False
    if not aws_manager.validate_credentials():
        error = True
        flash("Your AWS keys could not be validated. If this problem persists and you believe your keys are valid, "
              "please contact support.", canon_constants.STATUS_ERROR)
    elif ec2_security_group and not aws_manager.validate_security_group(ec2_security_group):
        error = True
        flash("Invalid EC2 security group", canon_constants.STATUS_ERROR)

    if error is True:
        return redirect(url_for('amazon'))

    account_manager = AccountManager(config)
    account_manager.add_aws_credentials(g.login, ec2_region, ec2_access_key, ec2_secret_key)

    account = account_manager.get_account(g.login)

    for instance in account.instances:
        instance.update_attribute('settings.create_acls_for_aws_ips', ['on'])

    flash("""Your AWS keys were successfully updated.
    If your AWS-synchronized ACLs are not applied within 30 minutes, please contact support.""",
          canon_constants.STATUS_OK)

    return redirect(url_for('amazon'))


@app.route('/external/delete_ec2_settings', methods=['POST'])
@viper_auth
def delete_ec2_settings():
    """Delete EC2 settings route."""
    try:
        account_manager = AccountManager(config)
        account_manager.delete_aws_credentials(g.login)
        flash('Your AWS keys were successfully deleted.', canon_constants.STATUS_OK)

    except Exception as ex:
        exception_uuid = Utility.obfuscate_exception_message(ex.message)
        flash_message = """There was a problem with deleting your AWS keys.
        If this problem persists, please contact support and provide Error ID {}.""".format(exception_uuid)
        flash(flash_message, canon_constants.STATUS_ERROR)
        Utility.log_traceback(config, exception_uuid)

    return redirect(url_for('amazon'))


@app.route('/external/rackspace')
@viper_auth
def rackspace():
    def obfuscate(str):
        return '{}{}'.format('*' * (len(str) - 4), str[-4:])

    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    obfuscated_rax_api_key = None

    if account.rax_username:
        obfuscated_rax_api_key = obfuscate(account.rax_api_key)

    return render_template('external/rackspace.html',
                           rax_username=account.rax_username,
                           obfuscated_rax_api_key=obfuscated_rax_api_key,
                           login=g.login)


@app.route('/external/add_rax_settings', methods=['POST'])
@viper_auth
def add_rax_settings():
    """Add Rackspace settings route."""

    rax_username = request.form.get('rax_username')
    rax_api_key = request.form.get('rax_api_key')
    rax_manager = RAXManager(config, rax_username, rax_api_key)

    error = False
    if not rax_manager.validate_credentials():
        error = True
        flash("Your Rackspace API key could not be validated. If this problem "
              "persists and you believe your keys are valid, please contact support.",
              canon_constants.STATUS_ERROR)

    if error is True:
        return redirect(url_for('rackspace'))

    account_manager = AccountManager(config)
    account_manager.add_rax_credentials(g.login, rax_username, rax_api_key)

    account = account_manager.get_account(g.login)

    for instance in account.instances:
        instance.update_attribute('settings.create_acls_for_rax_ips', ['on'])

    flash("Your Rackspace API key was successfully updated. If your Rackspace-synchronized "
          "ACLs are not applied within 30 minutes, please contact support.",
          canon_constants.STATUS_OK)

    return redirect(url_for('rackspace'))


@app.route('/external/delete_rax_settings', methods=['POST'])
@viper_auth
def delete_rax_settings():
    """Delete RAX settings route."""
    account_manager = AccountManager(config)
    account_manager.delete_rax_credentials(g.login)
    flash('Your Rackspace API key were successfully deleted.', canon_constants.STATUS_OK)
    return redirect(url_for('rackspace'))


@app.route('/add_shard/<selected_instance>', methods=['POST'])
@viper_auth
def add_shard(selected_instance):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if not instance:
        abort(404)

    instance.add_shard()
    Utility.log_to_db(config, "Shard added.", {'login': g.login, 'area': 'gui'})
    flash('Shard added successfully.', canon_constants.STATUS_OK)
    return redirect(url_for('instance_details', selected_instance=selected_instance))


@app.route('/add_acl/<instance>', methods=['POST'])
@viper_auth
def add_acl(instance):
    """Add instance ACL.

    Validates the supplied cidr_mask using netaddr.IPNetwork()
    Only valid IPv4 CIDR masks are allowed (or the special keyword "any")
    single IPs (1.2.3.4) are automatically converted to their /32 equiv (1.2.3.4/32)
    """
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, instance)

    cidr_mask = request.form['cidr_mask']
    description = request.form['description']

    if str(cidr_mask) == "0.0.0.0/0":
        cidr_mask = "any"

    # Logic to handle allow any with "ANY" keyword.
    if str(cidr_mask).lower().strip() == "any":
        user_instance.add_acl('0.0.0.0/1', "Allow Any")
        user_instance.add_acl('128.0.0.0/1', "Allow Any")
    else:
        # Validate cidr_mask by casting it using netaddr.IPNetwork
        # Casting also adds /32 to single IP CIDR masks
        try:
            cidr_net = IPNetwork(cidr_mask, version=4)
        except AddrFormatError:
            # Invalid CIDR mask provided
            flash_message = ("ACLs must be a valid IPv4 CIDR IP address, "
                             "or any to allow any source IP.  For assistance, please contact support.")
            flash(flash_message, canon_constants.STATUS_ERROR)
        else:
            # CIDR mask validated successfully
            user_instance.add_acl(str(cidr_net), description)

    return redirect(url_for('instance_details', selected_instance=instance))


@app.route('/delete_acl/<instance>', methods=['POST'])
@app.route('/delete_acl/<instance>/<acl_id>', methods=['POST'])
@viper_auth
def delete_acl(instance, acl_id=None):
    """Delete instance ACL."""
    if acl_id is None:
        acl_id = request.form['acl_id']

    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, instance)
    user_instance.delete_acl(acl_id)

    return redirect(url_for('instance_details', selected_instance=instance))


@app.route('/admin')
@viper_auth
@viper_isadmin
def admin():
    return redirect(url_for('admin_user_management'))


@app.route('/admin/billing')
@viper_auth
@viper_isadmin
def admin_billing():
    return render_template('admin/billing.html')


@app.route('/admin/error_logs')
@viper_auth
@viper_isadmin
def admin_error_logs():
    error_id = request.args.get('error_id')
    error = None
    if error_id is not None:
        audit_connection = Utility.get_audit_db_connection(config)
        log_collection = audit_connection[Constants.LOGS_COLLECTION]
        error = log_collection.find_one({'info.error_id': error_id})
    return render_template('admin/error_log.html', error=error, error_id=error_id)


@app.route('/admin/status_management')
@viper_auth
@viper_isadmin
def admin_status_management():
    status_manager = StatusManager(config)
    return render_template('admin/status_management.html', status=status_manager.get_status(),)


@app.route('/admin/user_management')
@viper_auth
@viper_isadmin
def admin_user_management():
    return render_template('admin/user_management.html')


@app.route('/admin/billing/associate_user', methods=['POST'])
@viper_auth
@viper_isadmin
def admin_associate_user():
    login = request.form['login']
    customer_id = request.form['customer_id']
    if not login or not customer_id:
        flash('Provide a valid UserID and CustomerID.', canon_constants.STATUS_ERROR)
        return redirect(url_for('admin_billing'))

    billing_manager = BillingManager(config)
    if billing_manager.associate_billing_account(login, customer_id):
        flash('Account "%s" has been associated with billing account "%s".'
              % (login, customer_id), 'ok')
        return redirect(url_for('admin_billing'))
    else:
        flash('Could not associate account "%s" with billing account "%s".'
              % (login, customer_id), canon_constants.STATUS_ERROR)
        return redirect(url_for('admin_billing'))


@app.route('/admin/billing/sync_user', methods=['POST'])
@viper_auth
@viper_isadmin
def admin_sync_user():
    if not request.form.get('login', None):
        flash('Provide a valid account login.', canon_constants.STATUS_ERROR)
        return redirect(url_for('admin'))

    login = request.form['login']
    account_manager = AccountManager(config)
    billing_manager = BillingManager(config)
    account = account_manager.get_account(login)

    if account is None:
        flash('Could not find account for "%s"' % login, canon_constants.STATUS_ERROR)
        return redirect(url_for('admin_billing'))
    else:
        if billing_manager.synchronize_billing_details(account.login):
            flash('Accounts have been synchronized for "%s".' % login, canon_constants.STATUS_OK)
        else:
            flash('Synchronization has failed. '
                  'More information has been logged to the database.', canon_constants.STATUS_ERROR)
        return redirect(url_for('admin_billing'))


@app.route('/admin/billing/set_user_invoiced', methods=['POST'])
@viper_auth
@viper_isadmin
def set_user_invoiced():
    account_name = request.form['invoiced_user']
    try:
        billing_manager = BillingManager(config)
        billing_manager.mark_account_as_manually_invoiced(account_name)
        flash('User {} marked as invoiced.'.format(account_name), canon_constants.STATUS_OK)
    except Exception:
        flash('Error marking user {} as invoiced: '.format(account_name), canon_constants.STATUS_ERROR)
    return redirect(url_for('admin_billing'))


@app.route('/admin/billing/set_invoiced_amount', methods=['POST'])
@viper_auth
@viper_isadmin
def set_invoice_amount():
    account_id = request.form['account_id']
    try:
        amount = request.form['amount']
        currency = request.form['currency']
        billing_manager = BillingManager(config)
        billing_manager.set_invoiced_amount(account_id, amount, currency)
        flash('Invoiced amount set as {} {} for account {}.'.format(amount, currency, account_id),
              canon_constants.STATUS_OK)
    except Exception as ex:
        flash('Error setting invoice amount for user {}: {}'.format(account_id, ex), canon_constants.STATUS_ERROR)
    return redirect(url_for('admin_billing'))


@app.route('/admin/billing/set_user_customplan', methods=['POST'])
@viper_auth
@viper_isadmin
def set_user_customplan():
    account_name = request.form['customplan_user']
    try:
        billing_manager = BillingManager(config)
        billing_manager.mark_account_with_custom_plan(account_name)
        flash('User {} marked with custom Stripe plan.'.format(account_name), canon_constants.STATUS_OK)
    except Exception as ex:
        flash('Error marking user {} with custom Stripe plan: {}'.format(account_name, ex),
              canon_constants.STATUS_ERROR)
    return redirect(url_for('admin_billing'))


@app.route('/admin/user_management/switch_user', methods=['POST'])
@viper_auth
@viper_isadmin
def admin_switch_user():
    user_id = request.form['switchuser']
    account_manager = AccountManager(config)
    if account_manager.get_account(user_id):
        session['login'] = user_id
        return redirect(url_for('instances'))
    else:
        flash('Provide a valid user to switch to.', canon_constants.STATUS_ERROR)
        return redirect(url_for('admin_user_management'))


@app.route('/admin/user_management/remove_user', methods=['POST'])
@viper_auth
@viper_isadmin
def admin_remove_user():
    login = request.form['login']
    billing_manager = BillingManager(config)
    account_manager = AccountManager(config)
    instance_manager = InstanceManager(config)

    account = account_manager.get_account(login)
    if account is None:
        flash('User "%s" does not exist.' % login, canon_constants.STATUS_ERROR)
    elif not account.active:
        flash('User "%s" is already deactivated.' % login, canon_constants.STATUS_WARNING)
    else:
        instance_manager.recycle_instances(account.login)

        if account.stripe_account:
            billing_manager.unsubscribe_customer(account.login)

        account_manager.deactivate_account(account.login)
        flash('User "%s" successfully deactivated' % login, 'ok')
    return redirect(url_for('admin_user_management'))


@app.route('/admin/status_management/add_message', methods=['POST'])
@viper_auth
@viper_isadmin
def admin_add_message():
        login = request.form.get('login', None)
        message = request.form.get('message', None)

        if not message:
            flash("Empty body, no message sent.", canon_constants.STATUS_ERROR)
        try:
            notifier = Notifier(config)
            if login:
                notifier.send_message(login, message)
            else:
                notifier.send_global_message(message)
            flash("Message posted", 'ok')
        except Exception as ex:
            flash("Message send failed: %s" % ex, canon_constants.STATUS_ERROR)
        return redirect(url_for('admin_status_management'))


@app.route('/admin/status_management/set_status', methods=['POST'])
@viper_auth
@viper_isadmin
def admin_set_status():
    status_manager = StatusManager(config)
    for i in request.form:
        status_manager.set_status(i, int(request.form[i]))
    flash('Status updated.', canon_constants.STATUS_OK)
    return redirect(url_for('admin_status_management'))


@app.route('/admin/inventory')
@viper_auth
@viper_isadmin
def admin_inventory():
    instance_manager = InstanceManager(config)
    # node_map = Utility.get_node_map(config)
    # TODO: Temp hack, get_node_map attempts to connect to all instances causing a timeout.
    node_map = {}
    checkouts = instance_manager.get_checkouts_by_type()
    return render_template('admin/inventory.html',
                           checkouts=checkouts,
                           node_map=node_map)


@app.route('/admin/revenue')
@viper_auth
@viper_isadmin
def admin_revenue():
    billing_manager = BillingManager(config)
    return render_template('admin/revenue.html',
                           revenue=billing_manager.get_billed_revenue())


@app.route('/admin/customer_reports')
@viper_auth
@viper_isadmin
def admin_customer_reports():
    account_manager = AccountManager(config)
    accounts_summary = account_manager.accounts_summary
    return render_template('admin/customer_reports.html',
                           accounts_summary=accounts_summary,
                           account_manager=account_manager)


@app.route('/admin/customer_reports/export')
@viper_auth
@viper_isadmin
def admin_export_customer_report():
    return Response(AccountManager(config).get_csv_report(),
                    mimetype='text/csv')


@app.route('/admin/instance_management')
@viper_auth
@viper_isadmin
def admin_instance_management():
    return render_template('admin/instance_management.html')


@app.route('/admin/instance_management/create_instance', methods=['POST'])
@viper_auth
@viper_isadmin
def admin_create_instance():
    account_name    = request.form['account_name']
    name            = request.form['name']
    plan_size_in_gb = int(request.form['plan'])
    service_type    = request.form['service_type']
    version         = request.form['version']
    zone            = request.form['zone']

    # HACK ALERT HACK ALERT HACK ALERT HACK ALERT
    if service_type == Constants.MONGODB_SERVICE:
        if int(plan_size_in_gb) == 1:
            instance_type = Constants.MONGODB_REPLICA_SET_INSTANCE
        else:
            instance_type = Constants.MONGODB_SHARDED_INSTANCE

    account_manager = AccountManager(config)
    account = account_manager.get_account(account_name)
    instance_manager = InstanceManager(config)

    if instance_manager.instance_exists(g.login, name):
        flash_message = "Cannot create instance '{}': an instance with this name already exists.".format(name)
        flash(flash_message, canon_constants.STATUS_ERROR)
        return redirect(url_for('admin_instance_management'))

    if not instance_manager.free_instance_count(plan_size_in_gb, zone, version, service_type, instance_type):
        flash_message = "Cannot create instance '{}': no instances available for plan {}, zone {}, version {}.".format(
            name, plan_size_in_gb, zone, version)
        flash(flash_message, canon_constants.STATUS_ERROR)

        subject = "Instance not available in UI."
        body = "Login {} attempted to add {} instance type {} with plan: {} zone: {} name: {}, version: {}".format(
            g.login, service_type, instance_type, plan_size_in_gb, zone, name, version)
        send_email(config.SUPPORT_EMAIL, subject, body)
        return redirect(url_for('admin_instance_management'))

    try:
        Utility.log_to_db(config, "Created instance.", {'login': g.login, 'area': 'gui', 'instance_name': name})
        account.add_instance(name, zone, plan_size_in_gb, version, service_type, instance_type)
    except Exception as ex:
        exception_uuid = Utility.obfuscate_exception_message(ex.message)
        flash_message = ("There was a problem creating an instance. If this problem persists please contact support "
                         "and provide Error ID {}.".format(exception_uuid))
        flash(flash_message, canon_constants.STATUS_ERROR)
        log_message = "Failed to create instance for login {}, plan {}, zone {}, name {}: {}".format(g.login,
                                                                                                     plan_size_in_gb,
                                                                                                     zone,
                                                                                                     name,
                                                                                                     ex)
        app.logger.error(log_message)

    return redirect(url_for('admin_instance_management'))


@app.route('/<instance_name>/compact', methods=['POST'])
@viper_auth
def compact_instance(instance_name):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, instance_name)

    if not instance.stepdown_scheduled:
        flash('Please schedule a stepdown window for before requesting compaction.', 'warning')
        return redirect(url_for('instance_details', selected_instance=instance_name))

    compaction_state = instance.compression.get(Constants.COMPACTION_STATE)
    acceptable_states = (None, Constants.COMPACTION_STATE_COMPRESSED, Constants.COMPACTION_STATE_ABORTED)
    if compaction_state not in acceptable_states:
        flash('Instance %s is currently undergoing compaction.' % instance.name, Constants.FLASH_ERROR)
        return redirect(url_for('instance_details', selected_instance=instance_name))

    instance.request_compression()
    flash('Compaction requested for instance %s.' % instance.name, 'ok')
    return redirect(url_for('instance_details', selected_instance=instance_name))


@app.route('/instances/<selected_instance>/repair', methods=['POST'])
@exclude_admin_databases(check_argument='selected_database')
@viper_auth
def repair_database(selected_instance):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    selected_database = request.form.get('database-name')
    if instance.repair_state:
        flash('Database %s has already been scheduled for repair.' % selected_database, Constants.FLASH_WARN)
    elif instance.get_database(selected_database) is None:
        flash('No database was selected for repair.', Constants.FLASH_WARN)
    else:
        instance.start_repairing_database(selected_database)
        flash('Database %s has been scheduled for repair.' % selected_database, 'ok')
    return redirect(url_for('instance_details', selected_instance=selected_instance))


@app.route('/instances/<selected_instance>/settings')
@viper_auth
def instance_settings(selected_instance):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if user_instance is None:
        abort(404)

    account_monitor = monitor.AccountMonitor(config)
    account_monitoring_checks = account_monitor.get_enabled_checks(asset_type=monitor.INSTANCE_ASSET_TYPE,
                                                                   user_controllable_only=True)

    for key in ['start', 'end']:
        if key in user_instance.stepdown_window:
            try:
                user_instance.stepdown_window[key] = user_instance.stepdown_window[key].strftime('%m/%d/%Y %H:%M')
            except AttributeError:
                user_instance.stepdown_window[key] = ''

    return render_template('settings/settings.html', account_monitoring_checks=account_monitoring_checks, instance=user_instance)


@app.route('/update_settings/<selected_instance>', methods=['POST'])
@viper_auth
def update_settings(selected_instance):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    stepdown_window = {
        'enabled': request.form.get('stepdown_window_enabled', 'off') == 'on',
        'scheduled': request.form.get('stepdown_scheduled', 'off') == 'on',
        'window_start': request.form.get('stepdown_window_start', '').strip(),
        'window_end': request.form.get('stepdown_window_end', '').strip(),
        'weekly': request.form.get('stepdown_window_weekly', 'off') == 'on',
    }

    for key in ['window_start', 'window_end']:
        if stepdown_window[key] == '':
            continue
        try:
            stepdown_window[key] = datetime.datetime.strptime(stepdown_window[key], '%m/%d/%Y %H:%M')
        except ValueError:
            flash('Invalid stepdown window specified. Dates must be in the month/day/year hour:minute format.', Constants.FLASH_ERROR)
            return redirect(url_for('instance_settings', selected_instance=selected_instance))

    if (isinstance(stepdown_window['window_start'], datetime.datetime) and
            isinstance(stepdown_window['window_end'], datetime.datetime) and
            stepdown_window['window_start'] >= stepdown_window['window_end']):
        flash('Invalid stepdown window specified. Start date must be earlier than the end date.', Constants.FLASH_ERROR)
        return redirect(url_for('instance_settings', selected_instance=selected_instance))

    settings_data = dict(request.form)

    for key in ('stepdown_window_enabled', 'stepdown_window_start', 'stepdown_window_end', 'stepdown_scheduled'):
        settings_data.pop(key)

    instance.update_settings(settings_data)
    instance.set_stepdown_window(**stepdown_window)
    instance.update_attribute('stepdown_window.ran_in_window', False)

    flash('Settings successfully updated.')
    return redirect(url_for('instance_settings', selected_instance=selected_instance))


@app.route('/system/status')
@viper_auth
def system_status():
    status_manager = StatusManager(config)
    return render_template('system_status/system_status.html', status=status_manager.get_status())


@app.route('/silence_alarm')
def silence_alarm():
    token = request.args.get('token')

    if token:
        try:
            annunciator = Annunciator(config)
            serializer = itsdangerous.URLSafeTimedSerializer(config.ALARM_SIGNING_KEY)
            alarm_id = serializer.loads(token, max_age=config.ALARM_SILENCE_TOKEN_TTL_IN_SECONDS)
            annunciator.mark_alarm_as_silenced(alarm_id)

            flash("Your alarm has been silenced.")
            return redirect(url_for('sign_in'))

        except itsdangerous.BadSignature:
            app.logger.info("Bad alarm silencing token presented: %s" % token)
            flash("Your alarm silencing token was invalid. Please try again.", canon_constants.STATUS_ERROR)
            return redirect(url_for('sign_in'))

        except Exception as ex:
            app.logger.info("Error silencing alarm: %s" % ex)
            flash("There was a problem silencing this alarm. Please try again.", canon_constants.STATUS_ERROR)
            return redirect(url_for('sign_in'))

    else:
        flash("Your alarm silencing token was invalid.", canon_constants.STATUS_ERROR)
        return redirect(url_for('sign_in'))


@app.route('/remote/instance')
@viper_auth
def remote_instance():
    reserved_networks = Utility.get_reserved_networks(config)
    return render_template('remote/remote_instance.html', reserved_networks=reserved_networks)


@app.route('/remote/instance/add', methods=['POST'])
@viper_auth
def add_remote_instance():
    instance_name = request.form['instance_name']
    connection_string = request.form['connection_string']
    admin_username = request.form.get('admin_username')
    admin_password = request.form.get('admin_password')

    hosts = connection_string.split(',')

    ssl = 'ssl' in request.form

    # Verify no host is in the blacklist.
    for hoststring in [host.split(':')[0] for host in hosts]:
        valid_host = False
        try:
            host = Host(hoststring)
            reserved_networks = Utility.get_reserved_networks(config)
            if host.is_routable() and not host.in_cidr_list(reserved_networks):
                valid_host = True
        except InvalidHost:
                pass
        finally:
            if not valid_host:
                flash("Invalid host {}.".format(hoststring), canon_constants.STATUS_ERROR)
                return redirect(url_for('remote_instance'))

    # Ensure given info is sufficient for proper connectivity.
    try:
        client = ClientWrapper(hosts, ssl=ssl)

    except SslConnectionFailure:
        flash("Unable to establish SSL connection to remote instance.", canon_constants.STATUS_ERROR)
        return redirect(url_for('remote_instance'))
    except ConnectionFailure:
        flash("Unable to establish connection to remote instance.", canon_constants.STATUS_ERROR)
        return redirect(url_for('remote_instance'))

    # Authenticate if necessary.
    auth_info = {}
    if admin_username and admin_password:
        try:
            admin_db = client.admin_db
            admin_db.authenticate(admin_username, admin_password)
        except OperationFailure:
            flash("Unable to authenticate with remote instance.", canon_constants.STATUS_ERROR)
            return redirect(url_for('remote_instance'))

        try:
            if client.is_replicated and not client.is_primary:
                flash("Unable to establish connection to remote instance primary.", canon_constants.STATUS_ERROR)
                return redirect(url_for('remote_instance'))
        except OperationFailure:
            flash("Unable to determine instance state. Please check user privileges.", canon_constants.STATUS_ERROR)
            return redirect(url_for('remote_instance'))

        try:
            # TODO: Refactor
            import random
            import string
            username = 'objectrocket_{}'.format(''.join([random.choice(string.ascii_letters) for i in range(12)]))
            plain_text_password = ''.join([random.choice(string.ascii_letters) for i in range(64)])
            encrypted_password = Utility.encrypt(config, plain_text_password)
            auth_info = {'admin': {'name': username, 'password': plain_text_password}}
            client.add_admin_user(**auth_info['admin'])
            auth_info['admin']['password'] = encrypted_password
        except OperationFailure:
            flash("Unable to add objectrocket user to remote instance. Please check user privileges.",
                  canon_constants.STATUS_ERROR)
            return redirect(url_for('remote_instance'))

    connection_info = {'host': connection_string, 'ssl': ssl}
    feature_info = client.feature_info
    server_info = client.server_info()

    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)

    account.add_remote_instance(instance_name, connection_info, auth_info, feature_info, server_info)

    flash("Remote instance successfully added.", canon_constants.STATUS_OK)
    return redirect(url_for('instances'))


@app.route('/remote/instance/remove', methods=['POST'])
@viper_auth
def remove_remote_instance():
    remote_instance_name = request.form['remote_instance_name']
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    account.remove_remote_instance(remote_instance_name)
    flash("Remote instance successfully removed.", canon_constants.STATUS_OK)
    return redirect(url_for('instances'))


@app.route('/remote/instance/<selected_instance>')
@viper_auth
def remote_instance_details(selected_instance):
    """Remote instance details page."""
    remote_instance_manager = RemoteInstanceManager(config)
    remote_instance = remote_instance_manager.get_remote_instance({Constants.LOGIN: g.login,
                                                                   Constants.NAME: selected_instance})
    if not remote_instance:
        abort(404)
    backups = remote_instance_manager.get_backup_history(g.login, selected_instance)
    return render_template('remote/remote_instance_details.html', backups=backups, remote_instance=remote_instance)


@app.route('/remote/instance/rename', methods=['POST'])
@viper_auth
def rename_remote_instance():
    current_remote_name = request.form['current_remote_name']
    new_remote_name = request.form['new_remote_name']
    remote_instance_manager = RemoteInstanceManager(config)

    if not current_remote_name:
        message = "Cannot rename an empty remote instance name"
        flash(message, canon_constants.STATUS_ERROR)
        return redirect(url_for('instances'))

    if not new_remote_name:
        message = "Cannot rename remote instance {}: A non-empty new instance name is required.".format(new_remote_name)
        flash(message, canon_constants.STATUS_ERROR)
        return redirect(url_for('instances'))

    if remote_instance_manager.remote_instance_exists(g.login, new_remote_name):
        message = ("Cannot rename remote instance {} to {}:",
                   "An remote instance named {} already exists.".format(current_remote_name, new_remote_name,
                                                                        new_remote_name))
        flash(message, canon_constants.STATUS_ERROR)
        return redirect(url_for('instances'))

    remote_instance_manager.rename_remote_instance(g.login, current_remote_name, new_remote_name)
    flash('Instance successfully renamed.', canon_constants.STATUS_OK)
    return redirect(url_for('instances'))


@app.route('/remote/database/<selected_instance>/<selected_database>')
@viper_auth
def remote_database_details(selected_instance, selected_database):
    remote_instance_manager = RemoteInstanceManager(config)
    remote_instance = remote_instance_manager.get_remote_instance({'login': g.login, 'name': selected_instance})
    database = remote_instance.client.get_database(selected_database)
    return render_template('remote/remote_database_details.html', remote_instance=remote_instance, database=database)


@app.route('/remote/database/user/add', methods=['POST'])
@viper_auth
def add_remote_database_user():
    database_name = request.form['database_name']
    instance_name = request.form['instance_name']
    username = request.form['username']
    password = request.form['password']
    remote_instance_manager = RemoteInstanceManager(config)
    remote_instance = remote_instance_manager.get_remote_instance({'login': g.login, 'name': instance_name})
    database = remote_instance.client.get_database(database_name)
    database.add_user(username, password=password, roles=["readWrite"])
    database.collection_names()
    flash('User added successfully.', canon_constants.STATUS_OK)
    return redirect(url_for('remote_instance_details', selected_instance=instance_name))


@app.route('/remote/database/user/remove', methods=['POST'])
@viper_auth
def remove_remote_database_user():
    database_name = request.form['database_name']
    instance_name = request.form['instance_name']
    username = request.form['username']
    remote_instance_manager = RemoteInstanceManager(config)
    remote_instance = remote_instance_manager.get_remote_instance({'login': g.login, 'name': instance_name})
    database = remote_instance.client.get_database(database_name)
    database.remove_user(username)
    flash('User removed successfully.', canon_constants.STATUS_OK)
    return redirect(url_for('remote_database_details', selected_instance=instance_name,
                            selected_database=database_name))


@app.route('/remote/database/drop', methods=['POST'])
@viper_auth
def drop_remote_database():
    database_name = request.form['database_name']
    instance_name = request.form['instance_name']
    remote_instance_manager = RemoteInstanceManager(config)
    remote_instance = remote_instance_manager.get_remote_instance({'login': g.login, 'name': instance_name})
    remote_instance.client.drop_database(database_name)
    flash('Database dropped successfully.', canon_constants.STATUS_OK)
    return redirect(url_for('remote_instance_details', selected_instance=instance_name))


@app.route('/remote/collection/<selected_instance>/<selected_database>/<selected_collection>')
@viper_auth
def remote_collection_details(selected_instance, selected_database, selected_collection):
    remote_instance_manager = RemoteInstanceManager(config)
    remote_instance = remote_instance_manager.get_remote_instance({'login': g.login, 'name': selected_instance})
    database = remote_instance.client.get_database(selected_database)
    collection = database.get_collection(selected_collection)
    return render_template('remote/remote_collection_details.html', collection=collection, database=database,
                           remote_instance=remote_instance)


@app.route('/remote/collection/create', methods=['POST'])
@viper_auth
def create_remote_collection():
    # TODO: Add options for the following
    # size: desired initial size for the collection (in bytes). For capped collections this size is the max size of the collection.
    # capped: if True, this is a capped collection
    # max: maximum number of objects if capped (optional)

    database_name = request.form['database_name']
    instance_name = request.form['instance_name']
    collection_name = request.form['collection_name']
    all_shard_keys = request.form.get('all_shard_keys')

    remote_instance_manager = RemoteInstanceManager(config)
    remote_instance = remote_instance_manager.get_remote_instance({'login': g.login, 'name': instance_name})
    database = remote_instance.client.get_database(database_name)

    if all_shard_keys:
        collection = database.get_collection(collection_name)
        collection.create_index(all_shard_keys)
    else:
        database.create_collection(collection_name)
    flash('Collection created successfully.', canon_constants.STATUS_OK)
    return redirect(url_for('remote_database_details', selected_instance=instance_name,
                            selected_database=database_name))


@app.route('/remote/collection/drop', methods=['POST'])
@viper_auth
def drop_remote_collection():
    pass


@app.route('/remote/collection/rename', methods=['POST'])
@viper_auth
def rename_remote_collection():
    pass


@app.route('/remote/index/create', methods=['POST'])
@viper_auth
def create_remote_index():
    #TODO: move to util, include in create_remote_collection
    def decode_json_list(data):
        items = []
        for item in data:
            if isinstance(item, tuple):
                try:
                    item = (item[0], int(item[1]))
                except ValueError:
                    pass
            items.append(item)
        return items

    database_name = request.form['database_name']
    instance_name = request.form['instance_name']
    collection_name = request.form['collection_name']
    all_index_keys = request.form['all_index_keys']
    background = request.form.get('background', True)
    drop_dups = request.form.get('dropdups')
    index_name = request.form.get('name')
    unique = request.form.get('unique')

    _kwargs = dict(background=background, dropdups=drop_dups, index_name=index_name, unique=unique)
    kwargs = {k: v for k, v in _kwargs.items() if v}
    index_keys = json.loads(all_index_keys, object_pairs_hook=decode_json_list)

    remote_instance_manager = RemoteInstanceManager(config)
    remote_instance = remote_instance_manager.get_remote_instance({'login': g.login, 'name': instance_name})
    database = remote_instance.client.get_database(database_name)
    collection = database.get_collection(collection_name)
    collection.create_index(index_keys, **kwargs)

    flash('Index created successfully.', canon_constants.STATUS_OK)
    return redirect(url_for('remote_collection_details', selected_instance=instance_name,
                            selected_database=database_name, selected_collection=collection_name))


@app.route('/remote/index/drop', methods=['POST'])
@viper_auth
def drop_remote_index():
    pass


@app.route('/api_token')
@viper_auth
def get_api_token():
    if "api_token" not in session:
        api_token_manager = tokens.APITokenManager(config)
        session.api_token = api_token_manager.create_token(account=g.login)

    return json.dumps({'api_token': session.api_token, 'user': g.login}), 200, {'content-type': 'application/json'}


@app.route('/api_urls')
@viper_auth
def get_api_urls():
    api_urls = {
        "apiv2": config.DEFAULT_API_ENDPOINT
    }

    return json.dumps(api_urls), 200, {'content-type': 'application/json'}
