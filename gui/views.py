"""GUI application views."""
from __future__ import division

# STL imports.
import collections
import datetime
import json
import locale
import urllib

# 3rd party imports.
import bson
import itsdangerous
import requests
import stripe

# 3rd part from imports.
from flask import abort, Response
from flask import flash, request, render_template, session, redirect, url_for, g
from flask import make_response
from flaskext.kvsession import KVSessionExtension
from functools import wraps
from pymongo.errors import AutoReconnect
from viper import config
from werkzeug.datastructures import ImmutableMultiDict

# ObjectRocket from imports.
from canon import constants as canon_constants
from viper import monitor
from viper.account import AccountManager
from viper.annunciator import Annunciator, Alarm
from viper.aws import AWSManager
from viper.billing import BillingManager, BillingException
from viper.constants import Constants
from viper.instance import InstanceManager
from viper.messages import MessageManager
from viper.mongo_instance import MongoDBInstanceException
from viper.mongo_sessions import MongoDBStore
from viper.notifier import Notifier
from viper.replica import ReplicaException
from viper.shard import ShardManager, ShardException
from viper.status import StatusManager
from viper.utility import Utility, FlaskUtility

# Make app available in this scope.
from gui import app

# TODO: Refactor: Should be declared with app instantiation (__init.py__)
# Define crypto key for cookies
app.secret_key = "Super Secret Key"
app.signing_key = "ba71f41a91e947f680d879c08982d302"

# Session system.
store = MongoDBStore(config)
KVSessionExtension(store, app)

# TODO: sniff userLanguage from navigator.language js and set locale from this
locale.setlocale(locale.LC_ALL, '')

# TODO: Refactor: Should move out of controllers into runserver or app (app resides in gui/__init__.py ... I'd move the app decl out of here)
# -----------------------------------------------------------------------
# Configure application logging
# -----------------------------------------------------------------------
if config.VIPER_IN_DEV:
    app.debug = True  # disabled in PRODUCTION, and forces logging to syslog
else:
    app.debug = False

if not app.debug:
    import logging
    from logging.handlers import SysLogHandler
    viper_syslog = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_LOCAL6)
    viper_syslog.setLevel(logging.DEBUG)

    viper_formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
    viper_syslog.setFormatter(viper_formatter)

    app.logger.setLevel(logging.DEBUG)
    app.logger_name = "gui"
    app.logger.addHandler(viper_syslog)

    app.logger.debug("Starting Viper")


# TODO: Refactor: Should move to a Utility lib
# -----------------------------------------------------------------------
# Viper Decorators
# -----------------------------------------------------------------------
def viper_auth(func):
    """Decorator to test for auth.

    Set session info to g.session, and redirect the user to the log in page
    if they aren't already signed in.
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
    flash("There has been an error with your replica instance. Please contact support@objectrocket.com")
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


@app.context_processor
def inject_constants():
    return {'Constants': Constants}


@app.context_processor
def inject_login():
    login = getattr(g, 'login', None)
    if login is not None:
        return {'login': login}
    return {}


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


@app.route('/api_timeseries/<name>/<selected_instance>', methods=['GET'])
@viper_auth
def api_timeseries(name, selected_instance):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    if instance is None:
        return ''
    return instance.get_timeseries_data(name)


@app.route('/api_serverStatus/<selected_instance>', methods=['GET'])
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
@app.route('/', methods=['GET'])
@viper_auth
def root():
    """Root url."""
    return redirect(url_for('sign_in'))


@app.route('/error', methods=['GET'])
def error():
    login = session.get('login', '')
    error_id = session.pop('error_id', '')
    return render_template('500.html', login=login, error_id=error_id, support_email=config.SUPPORT_EMAIL)


@app.route('/account')
@viper_auth
def account():
    """Account settings and controls."""
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    if account is None:
        return redirect(url_for('sign_in'))

    return render_template('account/account.html', account=account, login=g.login)


@app.route('/update_account_contact', methods=['POST'])
@viper_auth
def update_account_contact():
    """Update account contact info."""
    company = request.form['company']
    email = request.form['email']
    name = request.form['name']
    phone = request.form['phone']
    zipcode = request.form['zipcode']

    app.logger.debug(company+email+name+phone+zipcode)

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


@app.route('/instances/<selected_instance>/stats', methods=['GET'])
@viper_auth
def instance_stats(selected_instance):
    """Instance statistics page."""
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    instance = account.get_instance_by_name(selected_instance)

    return render_template('instances/instance_stats.html', instance=instance)


@app.route('/instances', methods=['GET'])
@viper_auth
def instances():
    """"Display account instances."""
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    instances = account.instances

    return render_template('instances/instances.html',
                           account=account,
                           api_keys=account.instance_api_keys,
                           instances=instances,
                           login=g.login,
                           Utility=Utility,
                           default_mongo_version=config.DEFAULT_MONGO_VERSION,
                           stripe_pub_key=config.STRIPE_PUB_KEY)


@app.route('/create_instance', methods=['POST'])
@viper_auth
def create_instance():
    name = request.form['name']
    plan_size_in_gb = int(request.form['plan'])
    service_type = request.form['service_type']
    version = request.form['version']
    zone = request.form['zone']

    # HACK ALERT HACK ALERT HACK ALERT HACK ALERT
    if service_type == Constants.MONGODB_SERVICE:
        if int(plan_size_in_gb) == 1:
            instance_type = Constants.MONGODB_REPLICA_SET_INSTANCE
        else:
            instance_type = Constants.MONGODB_SHARDED_INSTANCE

    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)

    instance_manager = InstanceManager(config)

    if instance_manager.instance_exists(g.login, name):
        flash_message = "Cannot create instance '%s': an instance with this name already exists." % name
        flash(flash_message, canon_constants.STATUS_ERROR)
        return redirect(url_for('instances'))

    if not instance_manager.free_instance_count(plan_size_in_gb, zone, version, service_type, instance_type):
        flash_message = ("Cannot create instance '%s': no instances are available for plan %s, zone %s, version %s."
                         % (name, plan_size_in_gb, zone, version))
        flash(flash_message, canon_constants.STATUS_ERROR)

        subject = "Instance not available in UI."
        body = "Login %s attempted to add %s instance type %s with plan: %s zone: %s name: %s, version: %s" % (
            g.login, service_type, instance_type, plan_size_in_gb, zone, name, version)
        send_email(config.SUPPORT_EMAIL, subject, body)
        return redirect(url_for('instances'))

    if len(account.instances) < config.MAX_INSTANCES_PER_USER:
        try:
            Utility.log_to_db(config, "Created instance.",
                              {'login': g.login, 'area': 'gui', 'instance_name': name})
            account.add_instance(name, zone, plan_size_in_gb, version, service_type, instance_type)
        except Exception as ex:
            exception_uuid = Utility.obfuscate_exception_message(ex.message)
            flash_message = ("There was a problem creating an instance. If this problem persists, contact"
                             "support and provide Error ID %s." % (exception_uuid))
            flash(flash_message, canon_constants.STATUS_ERROR)

            log_message = "Failed to create instance for login %s, plan %s, zone %s, name %s: %s" % (g.login, plan_size_in_gb, zone, name, ex)
            app.logger.error(log_message)
            return redirect(url_for('instances'))
    else:
        flash_message = "Please contact support if you need more than %d instances"
        flash(flash_message % config.MAX_INSTANCES_PER_USER, canon_constants.STATUS_WARNING)

    # return redirect(url_for('instance_details', selected_instance=name))
    return redirect(url_for('instances'))


@app.route('/instances/create', methods=['GET'])
@viper_auth
def instances_create():
    """"Create user instances."""
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    instances = account.instances

    return render_template('instances/instances_create.html',
                           account=account,
                           api_keys=account.instance_api_keys,
                           instances=instances,
                           login=g.login,
                           Utility=Utility,
                           default_mongo_version=config.DEFAULT_MONGO_VERSION,
                           stripe_pub_key=config.STRIPE_PUB_KEY)


@app.route('/<instance_name>/delete', methods=['POST'])
@viper_auth
def delete_instance(instance_name):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, instance_name)
    instance_manager.recycle_instance(instance.id)
    return redirect(url_for('instances'))


@app.route('/instances/<selected_instance>', methods=['GET', 'POST'])
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
    balancer = None
    shard_logs = None
    stepdown_window = user_instance.stepdown_window

    for key in ['start', 'end']:
        if key in stepdown_window:
            try:
                stepdown_window[key] = stepdown_window[key].strftime('%m/%d/%Y %H:%M')
            except AttributeError:
                stepdown_window[key] = ''

    stepdown_window.pop('election_started', None)

    try:
        databases = user_instance.databases
    except AutoReconnect:
        databases = None

    if user_instance.type == Constants.MONGODB_SHARDED_INSTANCE:
        shard_logs = user_instance.shard_logs
        balancer = user_instance.balancer

    try:
        enable_copy_database = user_instance.instance_connection.server_info()['versionArray'] >= [2, 4, 0, 0]
    except Exception:
        enable_copy_database = False

    aggregate_stats = {}
    usage_totals = {}

    if user_instance.type == Constants.MONGODB_SHARDED_INSTANCE:
        shard_logs = user_instance.shard_logs
        balancer = user_instance.balancer

    aggregate_stats, usage_totals = _calculate_instance_space_usage(user_instance)

    # Get instance operation states
    database_compaction_state = user_instance.compression.get(user_instance.COMPACTION_STATE, None)

    database_copy_state = None
    copy_database_document = user_instance.document.get('copy_database', None)
    if copy_database_document:
        database_copy_state = copy_database_document.get('state', None)

    database_repair_state = False
    if user_instance.type == Constants.MONGODB_REPLICA_SET_INSTANCE:
        database_repair_state = user_instance.repair_state

    return render_template('instances/instance_details.html',
                           account_monitoring_checks=account_monitoring_checks,
                           aggregate_stats=aggregate_stats,
                           balancer=balancer,
                           databases=databases,
                           database_compaction_state=database_compaction_state,
                           database_copy_state=database_copy_state,
                           database_repair_state=database_repair_state,
                           enable_copy_database=enable_copy_database,
                           get_host_zone=Utility.get_host_zone,
                           instance=user_instance,
                           is_sharded_instance=user_instance.type == Constants.MONGODB_SHARDED_INSTANCE,
                           login=g.login,
                           max_databases_per_replica_set_instances=config.MAX_DATABASES_PER_REPLICA_SET_INSTANCE,
                           usage_totals=usage_totals,
                           shard_logs=shard_logs)


# TODO(Anthony): Move this logic to core.
def _calculate_instance_space_usage(instance):
    """Calculate instance usage totals and percentages."""
    aggregate_stats = {}
    usage_totals = {}

    # The total size in bytes of the data held in all database.
    total_data_size = 0

    # The total size in bytes of all indexes created on all databases.
    total_index_size = 0

    # The total size of the namespace files for all databases.
    total_ns_size = 0

    # The total size in bytes of the data files that hold the databases.
    total_file_size = 0

    # The total amount of space in bytes allocated to collections in all database for document storage.
    total_storage_size = 0

    if instance.type == Constants.MONGODB_SHARDED_INSTANCE:

        for shard in instance.shards:
            shard_stats = shard.replica_set.primary.aggregate_database_statistics
            aggregate_stats[shard.name] = shard_stats

            # Aggregate size stats across all shards.
            total_data_size += shard_stats[Constants.DATA_SIZE_IN_BYTES]
            total_index_size += shard_stats[Constants.INDEX_SIZE_IN_BYTES]
            total_ns_size += shard_stats[Constants.NAMESPACE_SIZE_IN_BYTES]
            total_file_size += shard_stats[Constants.FILE_SIZE_IN_BYTES]
            total_storage_size += shard_stats[Constants.STORAGE_SIZE_IN_BYTES]

    else:
        primary_stats = instance.replica_set.primary.aggregate_database_statistics
        total_data_size = primary_stats[Constants.DATA_SIZE_IN_BYTES]
        total_index_size = primary_stats[Constants.INDEX_SIZE_IN_BYTES]
        total_ns_size = primary_stats[Constants.NAMESPACE_SIZE_IN_BYTES]
        total_file_size = primary_stats[Constants.FILE_SIZE_IN_BYTES]
        total_storage_size = primary_stats[Constants.STORAGE_SIZE_IN_BYTES]

    # Serialize size totals.
    usage_totals['total_data_size'] = total_data_size
    usage_totals['total_index_size'] = total_index_size
    usage_totals['total_ns_size'] = total_ns_size
    usage_totals['total_file_size'] = total_file_size
    usage_totals['total_storage_size'] = total_storage_size

    # Get size in bytes.
    size_in_bytes = instance.maximum_capacity

    # Round percentage totals.
    data_percentage = (float(total_data_size) / float(size_in_bytes)) * 100
    index_percentage = (float(total_index_size) / float(size_in_bytes)) * 100
    ns_percentage = (float(total_ns_size) / float(size_in_bytes)) * 100
    storage_percentage = (float(total_storage_size) / float(size_in_bytes)) * 100
    remaining_percentage = 100 - data_percentage - index_percentage - ns_percentage - storage_percentage

    # Serialize percentage totals.
    usage_totals['percentages'] = {
        'data': data_percentage,
        'index': index_percentage,
        'ns': ns_percentage,
        'storage': storage_percentage,
        'remaining': remaining_percentage,
    }

    # Account for container extensions.
    if total_file_size + total_ns_size > size_in_bytes:
        overage = (total_file_size + total_ns_size) - size_in_bytes
        usage_totals['overage'] = overage

    # Calculate shard balance percentage per shard.
    for shard_name in aggregate_stats:
        shard_stats = aggregate_stats[shard_name]
        shard_file_size_in_bytes = shard_stats[Constants.FILE_SIZE_IN_BYTES]
        shard_stats[Constants.PERCENTAGE_OF_INSTANCE_FILE_SIZE] = round((float(shard_file_size_in_bytes) / float(total_file_size)) * 100, 2)

    return aggregate_stats, usage_totals


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
    return redirect(url_for('instance_details', selected_instance=new_name))


@app.route('/instances/<selected_instance>/cluster', methods=['GET', 'POST'])
@viper_auth
def cluster(selected_instance):
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if not instance:
        abort(404)
    elif instance.type != Constants.MONGODB_SHARDED_INSTANCE:
        return redirect(url_for('instance_details', selected_instance=selected_instance))

    return render_template('cluster.html', instance=instance, get_host_zone=Utility.get_host_zone)


@app.route('/add_instance_user/<selected_instance>', methods=['GET', 'POST'])
@viper_auth
def add_instance_user(selected_instance):
    """Adds a user to each database in this instance"""
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    user = request.form['username']
    password = request.form['password']

    for database in instance.databases:
        try:
            instance.add_user(database.name, user, password)
        except Exception as ex:
            exception_uuid = Utility.obfuscate_exception_message(ex.message)
            flash_message = ("There was a problem updating user information for instance %s. If "
                             "this problem persists, contact support and provide Error ID %s.")

            flash_message = flash_message % (instance.name, exception_uuid)

            error_info = {
                'path': request.path,
                'user': getattr(g, 'login', None),
                'context': 'gui'
            }
            Utility.log_traceback(config, exception_uuid, error_info)
            flash(flash_message, canon_constants.STATUS_ERROR)

    return redirect(url_for('instances'))


@app.route('/add_instance_user/<selected_instance>', methods=['GET', 'POST'])
@viper_auth
def add_instance_user(selected_instance):
    """Adds a user to each database in this instance"""
    instance_manager = InstanceManager(config)
    instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    user = request.form['username']
    password = request.form['password']

    for database in instance.databases:
        try:
            instance.add_user(database.name, user, password)
        except Exception as ex:
            exception_uuid = Utility.obfuscate_exception_message(ex.message)
            flash_message = ("There was a problem updating user information for instance %s. If "
                             "this problem persists, contact "
                             "<a mailto:%s>%s</a> and provide Error ID %s." )

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
@app.route('/create_instance_user/<selected_instance>', methods=['GET', 'POST'])
@app.route('/create_instance_user/<selected_instance>/<selected_database>', methods=['GET', 'POST'])
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

            if user_instance.has_database(selected_database):
                # The database exists, just add a user to it.
                user_instance.add_user(selected_database, user, password)

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


@app.route('/delete_instance_user/<selected_instance>/<selected_database>', methods=['GET', 'POST'])
@app.route('/delete_instance_user/<selected_instance>/<selected_database>/<username>', methods=['GET', 'POST'])
@exclude_admin_databases(check_argument='selected_database')
@viper_auth
def delete_instance_user(selected_instance, selected_database, username=None):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)

    if username is None:
        username = request.form['username']

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
                            selected_instance = selected_instance))


@app.route('/instances/<selected_instance>/<selected_database>', methods=['GET', 'POST'])
@exclude_admin_databases(check_argument='selected_database')
@viper_auth
def database(selected_instance, selected_database):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    user_database = user_instance.get_database(selected_database)

    is_sharded_instance = user_instance.type == Constants.MONGODB_SHARDED_INSTANCE
    default_autohash_on_id = is_sharded_instance and user_instance.plan < config.DEFAULT_AUTO_HASH_ON_ID_CUTOFF_IN_GB

    return render_template('instances/instance_database.html',
                           collections=user_database.collections,
                           database=user_database,
                           default_autohash_on_id=default_autohash_on_id,
                           instance=user_instance,
                           is_sharded_instance=is_sharded_instance,
                           login=g.login,
                           users=user_database.users)


@app.route('/instances/<selected_instance>/<selected_database>/<selected_collection>', methods=['GET', 'POST'])
@exclude_admin_databases(check_argument='selected_database')
@viper_auth
def collection(selected_instance, selected_database, selected_collection):
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    user_database = user_instance.get_database(selected_database)
    user_collection = user_database.get_collection(selected_collection)
    indexes = user_database.get_indexes(user_collection)
    shard_keys = user_database.get_shard_keys(user_collection)
    if user_instance.type == Constants.MONGODB_SHARDED_INSTANCE:
        chunks = user_instance.get_chunks(user_collection)
    else:
        chunks = []

    try:
        sample_document = json_prettify(user_database.get_sample_document(selected_collection))
    except ValueError:
        sample_document = None

    return render_template('instances/collection.html',
                           chunks=chunks,
                           collection=user_collection,
                           database=user_database,
                           indexes=indexes,
                           instance=user_instance,
                           login=g.login,
                           sample_document=sample_document,
                           shard_keys=shard_keys)


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
        flash_message = ("There was a problem creating this collection. If this problem persists, contact"
                         "support and provide Error ID %s." % (exception_uuid))
        flash(flash_message, canon_constants.STATUS_ERROR)
        app.logger.error(ex)

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


@app.route('/create_index/<selected_instance>/<selected_db>/<selected_collection>', methods=['GET', 'POST'])
@exclude_admin_databases(check_argument='selected_db')
@viper_auth
def create_index(selected_instance, selected_db, selected_collection):
    background = request.form.get('background', True)
    drop_dups = request.form.get('dropdups', False)
    index_name = request.form.get('name', '')
    unique = request.form.get('unique', False)

    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, selected_instance)
    user_database = user_instance.get_database(selected_db)

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
        flash_message = ("There was a problem creating this index. If this problem persists, contact"
                         "support and provide Error ID %s." % (exception_uuid))
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
                max_age = config.PASSWORD_RESET_TOKEN_TTL_IN_SECONDS
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
                max_age = config.PASSWORD_RESET_TOKEN_TTL_IN_SECONDS
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
    session.pop('login', None)
    if request.method == 'GET':
        return render_template('sign_in/sign_in.html')

    login = request.form['login']
    password = request.form['password']

    account_manager = AccountManager(config)
    if not account_manager.authenticated(login, password):
        flash('Sign in failed.', canon_constants.STATUS_ERROR)
        return render_template('sign_in/sign_in.html')

    session['login'] = login

    flash('Sign in successful.', canon_constants.STATUS_OK)

    account = account_manager.get_account(login)
    if not account.accepted_msa:
        return redirect(url_for('msa'))

    return redirect(url_for('instances'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    app.logger.debug("Running logout")
    session.pop('login', None)
    return redirect(url_for('sign_in'))


@app.route('/sign_up1', methods=['GET', 'POST'])
def sign_up1():
    """Sign up and create a user account."""

    if request.method == 'POST':
        # Request came from the pricing page.
        if 'pricing_plan' in request.form:
            return render_template('sign_up1.html',
                                   pricing_plan=request.form['pricing_plan'])
        else:
            account_manager = AccountManager(config)
            if not account_manager.get_account(request.form['login']):
                account_manager.create_account(request.form['login'],
                                               request.form['password'],
                                               request.form['email'],
                                               request.form['name'],
                                               request.form['company'],
                                               request.form['phone'],
                                               request.form['zipcode'])

                annunciator = Annunciator(config)

                annunciator.create_alarm(Constants.ACCOUNT_SIGNUP,
                                         request.form['login'],
                                         Alarm.INFO,
                                         request.form['login'],
                                         notify_once=True,
                                         supplemental_data=request.form['name'])

                login = request.form.get('login', None)
                if login:
                    session['login'] = login
                    if 'requested_plan' in request.form:
                        session['requested_plan'] = request.form['requested_plan']

                return redirect(url_for('sign_up2'))

            else:
                ## user already exists
                return render_template('sign_up/sign_up1.html', error="user_exists")

    else:
        return render_template('sign_up/sign_up1.html')


@app.route('/sign_up2', methods=['GET', 'POST'])
@viper_auth
def sign_up2():
    account_manager = AccountManager(config)
    account_id = account_manager.get_account(g.login).id
    return render_template('sign_up/sign_up2.html',
                           account_id=account_id,
                           default_mongo_version=config.DEFAULT_MONGO_VERSION,
                           login=g.login)


@app.route('/sign_up3', methods=['GET', 'POST'])
@viper_auth
def sign_up3():
    if 'plan' in request.form and 'name' in request.form and 'zone' in request.form:
        return render_template('sign_up/sign_up3.html',
                               login=g.login,
                               name=request.form['name'],
                               plan=request.form['plan'],
                               service_type=request.form['service_type'],
                               stripe_pub_key=config.STRIPE_PUB_KEY,
                               version=request.form['version'],
                               zone=request.form['zone'])
    else:
        return redirect(url_for('sign_up2'))


# @app.route('/sign_up_finish', methods=['POST'])
@app.route('/sign_up_finish', methods=['GET', 'POST'])  # FIXME: Killl this line.
@viper_auth
def sign_up_finish():
    """Final stage of sign up process."""
    name = request.form['name']
    plan = request.form['plan']
    service_type = request.form['service_type']
    version = request.form['version']
    zone = request.form['zone']

    annunciator = Annunciator(config)
    instance_manager = InstanceManager(config)
    billing_manager = BillingManager(config)

    # Choose shard or replica set instance based on plan size.
    if service_type == Constants.MONGODB_SERVICE:
        if int(plan) == 1:
            instance_type = Constants.MONGODB_REPLICA_SET_INSTANCE
        else:
            instance_type = Constants.MONGODB_SHARDED_INSTANCE

    free_instance_count = instance_manager.free_instance_count(plan, zone, version, service_type, instance_type)

    if not free_instance_count:
        annunciator.create_alarm(Constants.INSTANCE_UNAVAILABLE_EVENT,
                                 zone,
                                 Alarm.WARN,
                                 g.login,
                                 notify_once=True,
                                 cc_support=True,
                                 support_only=True,
                                 supplemental_data={'name': name, 'plan': plan})

    try:
        billing_manager.set_credit_card(g.login, request.form['stripe_token'])
    except stripe.CardError:
        app.logger.info("Credit card declined during signup for user {}".format(g.login))
        flash('There was a problem adding your credit card. Please try again.', canon_constants.STATUS_ERROR)
        return render_template('sign_up/sign_up3.html',
                               name=name,
                               plan=plan,
                               zone=zone,
                               version=version,
                               service_type=service_type)

    return render_template('sign_up/sign_up_finish.html',
                           free_instance_count=free_instance_count,
                           login=g.login,
                           name=name,
                           plan=plan,
                           service_type=service_type,
                           version=version,
                           zone=zone)


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
    invoices = {}
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
    valid_redirect_routes = [url_for('billing'), url_for('dashboard')]

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

    print(aws_manager.validate_credentials())

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
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(g.login, instance)

    cidr_mask = request.form['cidr_mask']
    description  = request.form['description']

    # Logic to handle allow any with "ANY" keyword.
    if str(cidr_mask).lower().strip() == "any":
        user_instance.add_acl('0.0.0.0/1', "Allow Any")
        user_instance.add_acl('128.0.0.0/1', "Allow Any")
    else:
        user_instance.add_acl(cidr_mask, description)

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


@app.route('/admin/inventory', methods=['GET'])
@viper_auth
@viper_isadmin
def admin_inventory():
    instance_manager = InstanceManager(config)
    node_map = Utility.get_node_map(config)
    checkouts=instance_manager.get_checkouts_by_type()
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


@app.route('/admin/customer_reports', methods=['GET'])
@viper_auth
@viper_isadmin
def admin_customer_reports():
    account_manager = AccountManager(config)
    accounts_summary = account_manager.accounts_summary
    return render_template('admin/customer_reports.html',
                           accounts_summary=accounts_summary,
                           account_manager=account_manager)


@app.route('/admin/customer_reports/export', methods=['GET'])
@viper_auth
@viper_isadmin
def admin_export_customer_report():
    return Response(AccountManager(config).get_csv_report(),
                    mimetype='text/csv')


@app.route('/admin/instance_management', methods=['GET'])
@viper_auth
@viper_isadmin
def admin_instance_management():
    return render_template('admin/instance_management.html')


from pprint import pprint
@app.route('/admin/instance_management/create_instance', methods=['POST'])
@viper_auth
@viper_isadmin
def admin_create_instance():
    pprint(request.form)
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

    compaction_state = instance.compression.get(instance.COMPACTION_STATE)
    acceptable_states = (None, instance.COMPACTION_STATE_COMPRESSED, instance.COMPACTION_STATE_ABORTED)
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


@app.route('/instances/<selected_instance>/settings', methods=['GET'])
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


@app.route('/system/status', methods=['GET'])
@viper_auth
def system_status():
    status_manager = StatusManager(config)
    return render_template('system_status/system_status.html', status=status_manager.get_status())
