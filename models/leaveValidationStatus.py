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

    @api.onchange('validators_type','holiday_validators_user','holiday_validators_position','approval')
    def prevent_change(self):
        raise UserError(_(
            "Changing leave validators is not permitted. You can only change "
            "it from Leave Types Configuration"))