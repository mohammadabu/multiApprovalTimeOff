import re
from datetime import datetime, timedelta
from odoo import models, api, fields, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import email_split
from pytz import timezone, UTC

class HrLeaveTypes(models.Model):
    """ Extend model to add multilevel approval """
    _inherit = 'hr.leave.type'

    multi_level_validation = fields.Boolean(string='Multiple Level Approval',
                                            help="If checked then multi-level approval is necessary")
    validation_type = fields.Selection(selection_add=[('multi', 'Multi Approvals')])
    leave_validators = fields.One2many('hr.holidays.validators',
                                       'hr_holiday_status',
                                       string='Leave Validators', help="Leave validators")

    # 5/6/2021
    yearsـofـservice = fields.Integer(string="Years of service") 
    # 5/6/2021 

    @api.onchange('validation_type')
    def enable_multi_level_validation(self):
        """ Enabling the boolean field of multilevel validation"""
        if self.validation_type == 'multi':
            self.multi_level_validation = True
        else:
            self.multi_level_validation = False

    @api.onchange('multi_level_validation')
    def disable_double_validation(self):
        """ Disable doy=uble validation when multi level a
        pproval is disabled """
        if self.multi_level_validation:
            self.double_validation = False

    @api.onchange('double_validation')
    def disable_multi_approval(self):
        """ Disable multi level approval when double validation is enabled """
        if self.double_validation:
            self.multi_level_validation = False

    def write(self,values):
        rtn = super(HrLeaveTypes,self).write(values)
        if self.validation_type == "multi":
            if len(self.leave_validators) < 1:
                raise UserError(_("At Least Add One leave_validators"))
        return rtn