import re
from datetime import datetime, timedelta
from odoo import models, api, fields, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import email_split
from pytz import timezone, UTC


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    commencement_business = fields.Date("Date of commencement of business")

    @api.model
    def create(self,vals):
        try:   
            if "commencement_business" in vals:
                _logger.info("---------------------------")
                _logger.info(vals['commencement_business'][0][2])
        except:
            _logger.info("An exception occurred")                                  
        rtn = super(HrEmployee,self).create(vals)
        return rtn 


