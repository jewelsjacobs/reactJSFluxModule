"""GUI application views."""
from flask import flash, g, redirect, render_template, request, session, url_for
from functools import wraps
from viper import config
from viper.account import AccountManager
from viper.annunciator import Alarm, Annunciator
from viper.billing import BillingManager, BillingException
from viper.constants import Constants
from viper.instance import InstanceManager

from gui import app


@app.route('/', methods=['GET', 'POST'])
def canon_test():
    return render_template('test.html')


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
            return render_template('sign_in.html')
    return internal


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
