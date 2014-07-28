"""WTForms module."""
from viper.constants import Constants

from flask_wtf import Form
from wtforms import fields
from wtforms import validators

VALID_SIZE_INPUT = [1, 5, 20, 50, 100]


# TODO(Anthony): Rafactor: do not key on the form to select 'service_type'.
def valid_version(form, field):
    """Ensure the given version is valid for the specified service type."""
    service = form['service_type'].data
    version = field.data

    if version not in Constants.SERVICE_VERSIONS_MAP[service]['versions']:
        raise validators.ValidationError('Invalid value "{}" for service "{}".'.format(version, service))


class CreateInstance(Form):
    """Form for instance creation."""

    name = fields.StringField('name', validators=[validators.Length(min=1, message='Instance name must be at least one character.')])
    plan = fields.IntegerField('plan', validators=[validators.AnyOf(values=VALID_SIZE_INPUT)])
    service_type = fields.RadioField('service_type',
                                     validators=[validators.AnyOf(values=Constants.SERVICE_VERSIONS_MAP.keys())],
                                     choices=[(Constants.MONGODB_SERVICE, Constants.SERVICE_DISPLAY_NAMES[Constants.MONGODB_SERVICE]),
                                              (Constants.TOKUMX_SERVICE, Constants.SERVICE_DISPLAY_NAMES[Constants.TOKUMX_SERVICE]),
                                              (Constants.REDIS_SERVICE, Constants.SERVICE_DISPLAY_NAMES[Constants.REDIS_SERVICE])])
    version = fields.HiddenField('version', validators=[valid_version])
    zone = fields.StringField('zone', validators=[validators.AnyOf(values=Constants.SERVER_ZONES, message='Invalid zone.')])
