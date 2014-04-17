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
from viper.shard import ShardManager
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

    Set session info to g.session, and redirect the user to the login page
    if they aren't already signed in.
    """
    @wraps(func)
    def internal(*args, **kwargs):
        if 'login' in session:
            g.login = session['login']
            return func(*args, **kwargs)
        else:
            return render_template('login/login.html')
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
                      Constants.FLASH_WARN)
                return redirect(url_for('default'))
        except Exception as ex:
            ex_info = '%s: %s' % (ex.__class__.__name__, ex)
            flash('Problem with admin function: %s' % ex_info,
                  Constants.FLASH_ERROR)
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
    flash("There has been an error with your account. Please contact {}".format(config.SUPPORT_EMAIL))
    app.logger.error(msg)
    return redirect(url_for('account'))


@app.errorhandler(MongoDBInstanceException)
def mongo_instance_exception_handler(error):
    msg = "Instance Error: {0}".format(error)
    flash("There has been an error with your mongo instance. Please contact support@objectrocket.com")
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


@app.route('/account')
@viper_auth
def account():
    """Account settings and controls."""
    account_manager = AccountManager(config)
    account = account_manager.get_account(g.login)
    if account is None:
        return redirect(url_for('login'))

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

    flash('Account successfully updated.', Constants.FLASH_INFO)

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

    flash('Password successfully updated.')
    return redirect(url_for('account'))


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
        flash(flash_message, Constants.FLASH_ERROR)
        return redirect(url_for('instances'))

    if not instance_manager.free_instance_count(plan_size_in_gb, zone, version, service_type, instance_type):
        flash_message = ("Cannot create instance '%s': no instances are available for plan %s, zone %s, version %s."
                         % (name, plan_size_in_gb, zone, version))
        flash(flash_message, Constants.FLASH_ERROR)

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
            flash_message = ("There was a problem creating an instance. If this problem persists, contact <a mailto:%s>%s</a> "
                             "and provide Error ID %s." % (config.SUPPORT_EMAIL, config.SUPPORT_EMAIL, exception_uuid))
            flash(flash_message, Constants.FLASH_ERROR)

            log_message = "Failed to create instance for login %s, plan %s, zone %s, name %s: %s" % (g.login, plan_size_in_gb, zone, name, ex)
            app.logger.error(log_message)
            return redirect(url_for('instances'))
    else:
        flash_message = "Please contact support if you need more than %d instances"
        flash(flash_message % config.MAX_INSTANCES_PER_USER, Constants.FLASH_WARN)

    # return redirect(url_for('instance_details', selected_instance=name))
    return redirect(url_for('instances'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/<selected_instance>', methods=['GET', 'POST'])
@viper_auth
def dashboard(selected_instance=None):
    ## ignore requests for favicon.ico to the gui
    # TODO: Reconfigure nginx to serve up /favicon.ico
    if selected_instance and selected_instance.lower() == "favicon.ico":
        abort(404)

    message_manager = MessageManager(config)
    account_manager = AccountManager(config)
    status_manager = StatusManager(config)

    account = account_manager.get_account(g.login)
    instances = account.instances
    messages = message_manager.get_messages(g.login, limit=5)

    if selected_instance is None:
        try:
            instance = instances[0]
        except IndexError:
            instance = None
    else:
        instance = account.get_instance_by_name(selected_instance)

    return render_template('dashboard/dashboard.html',
                           login=account.login,
                           has_instances=instance is not None,
                           instances=instances,
                           account=account,
                           status=status_manager.get_status(),
                           instance=instance,
                           messages=messages,
                           stripe_pub_key=config.STRIPE_PUB_KEY)


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


@app.route('/instances/<selected_instance>', methods=['GET', 'POST'])
@viper_auth
def instance_details(selected_instance):
    """Instance details page."""
    login = g.login

    if 'selected_tab' in request.args:
        selected_tab = request.args['selected_tab']
    else:
        selected_tab = 'databases'

    account_monitor = monitor.AccountMonitor(config)
    account_monitoring_checks = account_monitor.get_enabled_checks(asset_type=monitor.INSTANCE_ASSET_TYPE,
                                                                   user_controllable_only=True)
    instance_manager = InstanceManager(config)
    user_instance = instance_manager.get_instance_by_name(login, selected_instance)

    if user_instance is None:
        abort(404)

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

    all_shard_statistics = {}

    if user_instance.type == Constants.MONGODB_SHARDED_INSTANCE:
        shard_logs = user_instance.shard_logs
        sorted_shard_keys = sorted(shard_logs)
        balancer = user_instance.balancer

        instance_total_file_size_in_bytes = 0

        for shard in user_instance.shards:
            shard_statistics = shard.replica_set.primary.aggregate_database_statistics
            all_shard_statistics[shard.name] = shard_statistics
            instance_total_file_size_in_bytes += shard_statistics[Constants.FILE_SIZE_IN_BYTES]

        for shard_name in all_shard_statistics:
            shard_statistics = all_shard_statistics[shard_name]
            shard_file_size_in_bytes = shard_statistics[Constants.FILE_SIZE_IN_BYTES]
            shard_statistics[Constants.PERCENTAGE_OF_INSTANCE_FILE_SIZE] = shard_file_size_in_bytes / instance_total_file_size_in_bytes * 100

    return render_template('instances/instance_details.html',
                           account_monitoring_checks=account_monitoring_checks,
                           all_shard_statistics=all_shard_statistics,
                           balancer=balancer,
                           databases=databases,
                           enable_copy_database=enable_copy_database,
                           instance=user_instance,
                           is_sharded_instance=user_instance.type == Constants.MONGODB_SHARDED_INSTANCE,
                           login=login,
                           max_databases_per_replica_set_instances=config.MAX_DATABASES_PER_REPLICA_SET_INSTANCE,
                           selected_tab=selected_tab,
                           shard_logs=shard_logs,
                           sorted_shard_keys=sorted_shard_keys,
                           )


@app.route('/notifications')
@viper_auth
def notifications():
    """Display account notification messages."""
    message_manager = MessageManager(config)
    messages = message_manager.get_messages(g.login)

    # TODO(Anthony): Finish logic for gathering all alarms, filtering by instance, et cetera.
    alarms = []
    return render_template('notifications/notifications.html', alarms=alarms, login=g.login, messages=messages)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    session.pop('login', None)
    if request.method == 'GET':
        return render_template('login/login.html')

    login = request.form['login-input']
    password = request.form['password-input']

    account_manager = AccountManager(config)
    if not account_manager.authenticated(login, password):
        flash('Login failed.')
        return render_template('login/login.html')

    session['login'] = login

    flash('Login successful.')
    return redirect(url_for('instances'))

    # TODO(Anthony): Use these lines when ready.
    # account = account_manager.get_account(login)
    # if not account.accepted_msa:
    #     return redirect(url_for('msa'))

    return redirect(url_for('dashboard'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    app.logger.debug("Running logout")
    session.pop('login', None)
    return redirect(url_for('login'))


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
    except BillingException:
        app.logger.info("Credit card declined during signup for user {}".format(g.login))
        flash('There was a problem adding your credit card. Please try again.', Constants.FLASH_ERROR)
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

    try:
        billing_manager.set_credit_card(g.login, request.form['stripe_token'])
        flash('Credit card information updated.', Constants.FLASH_INFO)

    except stripe.CardError as ex:
        flash(ex.message, Constants.FLASH_ERROR)

    if 'returntarget' in request.form:
        return redirect(url_for(request.form['returntarget']))
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
