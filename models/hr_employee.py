import re
from datetime import datetime, timedelta
from odoo import models, api, fields, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import email_split
from pytz import timezone, UTC


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    commencement_business = fields.Date("Date of commencement of business")
    