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
            _logger.info("---------------------------")
            _logger.info(vals['commencement_business'])
            commencement_business = vals['commencement_business']
            annual_leave_type = self.env['hr.leave.type'].sudo().search(['&',('finished_carry_froword','=',False),'|','&',('validity_start','>=',commencement_business),('validity_stop','<=',commencement_business),'&',('validity_start','=',''),('validity_stop','=','')])
            _logger.info(annual_leave_type)
        except:
            _logger.info("An exception occurred")                                  
        rtn = super(HrEmployee,self).create(vals)
        return rtn 


