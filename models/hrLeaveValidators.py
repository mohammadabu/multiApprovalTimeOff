import re
from datetime import datetime, timedelta
from odoo import models, api, fields, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import email_split
from pytz import timezone, UTC


class HrLeaveValidators(models.Model):
    """ Model for leave validators in Leave Types configuration """
    _name = 'hr.holidays.validators'

    hr_holiday_status = fields.Many2one('hr.leave.type')
    validators_type = fields.Selection(
        [
            ('direct_manager','Direct Manager'),
            ('manager_of_manager','Manager of manager'),
            ('position','Position'),
            ('user','User')
        ]
    )
    holiday_validators_user = fields.Many2one('res.users',
                                         string='Leave Validators', help="Leave validators",
                                         domain="[('share','=',False)]")
    holiday_validators_position = fields.Many2one('hr.job')                                     
    approval = fields.Boolean()    