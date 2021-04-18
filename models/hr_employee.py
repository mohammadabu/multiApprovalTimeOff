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
            _logger.info(vals['company_id'])
            commencement_business = vals['commencement_business']
            annual_leave_type = self.env['hr.leave.type'].sudo().search(['&',('finished_carry_froword','=',False),'|',('validity_stop','>=',commencement_business),'&',('validity_start','=',False),('validity_stop','=',False)])
            _logger.info(annual_leave_type)
            for annual in annual_leave_type:
                annual_leave_allocation = self.env['hr.leave.allocation'].sudo().search([('holiday_status_id','=',annual.id),('state','=','validate')])
                for allocation in annual_leave_allocation:
                    # By Company
                    if allocation.holiday_type == "company":
                        if vals['company_id'] != False:
                            if allocation.mode_company_id == vals['company_id']:
                                self.env['hr.leave.allocation'].sudo().create({
                                    "name":allocation.name,
                                    "holiday_status_id":allocation.holiday_status_id,
                                    "allocation_type":allocation.allocation_type,
                                    "nextcall":allocation.nextcall,
                                    "number_per_interval":allocation.number_per_interval,
                                    "unit_per_interval":allocation.unit_per_interval,
                                    "interval_number":allocation.interval_number,
                                    "interval_unit":allocation.interval_unit,
                                    "holiday_type":"employee",
                                    "employee_id":vals['id'],
                                    "number_of_days_display":allocation.number_of_days_display
                                })
        except:
            _logger.info("An exception occurred")                                  
        rtn = super(HrEmployee,self).create(vals)
        return rtn 


