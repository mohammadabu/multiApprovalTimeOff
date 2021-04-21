import re
from datetime import datetime, timedelta
from odoo import models, api, fields, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import email_split
from pytz import timezone, UTC

class LeaveValidationStatus(models.Model):
    _name = 'leave.validation.status'

    holiday_status = fields.Many2one('hr.leave')

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
    validation_status = fields.Boolean(string='Approved', readonly=True,
                                       default=False,
                                       track_visibility='always', help="Approved")
    validation_refused = fields.Boolean(string='Refused', readonly=True,
                                       default=False,
                                       track_visibility='always', help="Refused")                                   
    leave_comments = fields.Text(string='Comments', help="Comments",readonly=True)
    exceptions = fields.Selection(
        [
            ('1d','Greater than  1 day'),
            ('2d','Greater than  2 day'),
            ('3d','Greater than  3 day'),
            ('4d','Greater than  4 day'),
            ('5d','Greater than  5 day'),
            ('6d','Greater than  6 day'),
            ('7d','Greater than  7 day'),
            ('8d','Greater than  8 day'),
            ('9d','Greater than  9 day'),
            ('10d','Greater than  10 day'),
            ('11d','Greater than  11 day'),
            ('12d','Greater than  12 day'),
            ('13d','Greater than  13 day'),
            ('14d','Greater than  14 day'),
            ('15d','Greater than  15 day'),
        ]
    )

    @api.onchange('validators_type','holiday_validators_user','holiday_validators_position','approval','exceptions')
    def prevent_change(self):
        raise UserError(_(
            "Changing leave validators is not permitted. You can only change "
            "it from Leave Types Configuration"))