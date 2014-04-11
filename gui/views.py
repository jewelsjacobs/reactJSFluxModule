"""GUI application views."""
import requests

from flask import abort, flash, g, redirect, render_template, request, session, url_for
from functools import wraps
from pymongo.errors import AutoReconnect
from viper import config
from viper import monitor
from viper.account import AccountManager
from viper.annunciator import Alarm, Annunciator
from viper.billing import BillingManager, BillingException
from viper.constants import Constants
from viper.instance import InstanceManager
from viper.utility import Utility

from gui import app


@app.context_processor
def inject_constants():
    """Inject Constants into our templates."""
    return {'Constants': Constants}


# TODO: Refactor: Needs refactor / error checking. Should be moved elsewhere if we actually need it.
def send_email(recipient, subject, body):
    return requests.post(
        "https://api.mailgun.net/v2/objectrocket.mailgun.org/messages",
        auth=("api", "key-9i3dch4p928wedoaj4atoqxoyxb-hy29"),
        data={"from": "ObjectRocket <support@objectrocket.com>",
              "to": recipient,
              "subject": subject,
              "text": body})


# TODO: Refactor: Should move to a Utility lib
def viper_auth(func):
    """Decorator to test for auth.

    Set session info to g.session, and redirect the user to the sign_in page
    if they aren't already signed in.
    """
    @wraps(func)
    def internal(*args, **kwargs):
        if 'login' in session:
            g.login = session['login']
            return func(*args, **kwargs)
        else:
            return render_template('sign_in/sign_in.html')
    return internal


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
    # ## ignore requests for favicon.ico to the gui
    # # TODO: Reconfigure nginx to serve up /favicon.ico
    # if selected_instance and selected_instance.lower() == "favicon.ico":
    #     abort(404)

    # message_manager = MessageManager(config)
    # account_manager = AccountManager(config)
    # status_manager = StatusManager(config)

    # account = account_manager.get_account(g.login)
    # instances = account.instances
    # messages = message_manager.get_messages(g.login, limit=5)

    # if selected_instance is None:
    #     try:
    #         instance = instances[0]
    #     except IndexError:
    #         instance = None
    # else:
    #     instance = account.get_instance_by_name(selected_instance)

    # return render_template('home.html',
    #                        login=account.login,
    #                        has_instances=instance is not None,
    #                        instances=instances,
    #                        account=account,
    #                        status=status_manager.get_status(),
    #                        instance=instance,
    #                        messages=messages,
    #                        stripe_pub_key=config.STRIPE_PUB_KEY)
    return 'BUILDING'


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


@app.route('/messages')
@viper_auth
def messages():
    # """Display user messages."""
    # message_manager = MessageManager(config)
    # messages = message_manager.get_messages(g.login)

    # return render_template('messages.html', messages=messages, login=g.login)
    return 'BUILDING'


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    """User sign in."""
    session.pop('login', None)
    if request.method == 'GET':
        return render_template('sign_in/sign_in.html')

    login = request.form['login-input']
    password = request.form['password-input']

    account_manager = AccountManager(config)
    if not account_manager.authenticated(login, password):
        flash('Sign in failed.')
        return render_template('sign_in.html')

    session['login'] = login

    flash('Sign in successful.')
    return redirect(url_for('instances'))

    # TODO(Anthony): Use these lines when ready.
    # account = account_manager.get_account(login)
    # if not account.accepted_msa:
    #     return redirect(url_for('msa'))

    # return redirect(url_for('default'))


# TODO: Refactor: This route effectively does nothing with GET. Remove GET from methods, remove request.method check and final else.
@app.route('/sign_up1', methods=['GET', 'POST'])
def sign_up1():
    """Sign up user; create account."""

    if request.method == 'POST':
        # request came from the pricing page
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
                return render_template('sign_up1.html', error="user_exists")

    else:
        return render_template('sign_up1.html')


# TODO: Refactor: Should use viper_auth.
@app.route('/sign_up2', methods=['GET', 'POST'])
def sign_up2():
    if 'login' in session:
        login = session['login']
    else:
        return redirect(url_for('sign_up1'))

    account_manager = AccountManager(config)
    account_id = account_manager.get_account(login).id
    return render_template('/sign_up2.html',
                           default_mongo_version=config.DEFAULT_MONGO_VERSION,
                           account_login=login,
                           account_id=account_id)


@app.route('/sign_up3', methods=['GET', 'POST'])
def sign_up3():
    if 'login' in session:
        login = session['login']
    else:
        return redirect(url_for('sign_up1'))

    if 'plan' in request.form and 'name' in request.form and 'zone' in request.form:
        return render_template('/sign_up3.html',
                               stripe_pub_key=config.STRIPE_PUB_KEY,
                               name=request.form['name'],
                               plan=request.form['plan'],
                               zone=request.form['zone'],
                               service_type=request.form['service_type'],
                               version=request.form['version'])
    else:
        return redirect(url_for('sign_up2'))


@app.route('/sign_up_finish', methods=['POST'])
@viper_auth
def sign_up_finish():
    """Final stage of signup process."""
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
        return render_template('/sign_up3.html',
                               name=name,
                               plan=plan,
                               zone=zone,
                               version=version,
                               service_type=service_type)

    return render_template('/sign_up_finish.html',
                           name=name,
                           plan=plan,
                           zone=zone,
                           service_type=service_type,
                           version=version,
                           free_instance_count=free_instance_count)
