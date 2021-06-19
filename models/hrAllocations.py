import re
from datetime import datetime,date, timedelta
from odoo import models, api, fields, _
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import email_split
from pytz import timezone, UTC


class HrAllocations(models.Model):
    _inherit = 'hr.leave.allocation'
    allocation_carry_forword = fields.Boolean()
    
    def custom_leave_for_this_year(self):     
        _logger.info("---------------------------")
        current_date = datetime.now().date()
        annual_leave_allocation = self.env['hr.leave.allocation'].sudo().search([('allocation_carry_forword','=',False),('parent_id','!=',False)])
        for annual in annual_leave_allocation:
            if annual.employee_id != False:
                annual_leave_type = self.env['hr.leave.type'].sudo().search(['&',('id','=',annual.holiday_status_id.id),'&',('validity_start','!=',False),('validity_stop','!=',False)])
                validity_stop = annual_leave_type.validity_stop
                validity_start = annual_leave_type.validity_start
                if annual.employee_id.commencement_business == False or annual.employee_id.commencement_business < validity_start:
                    commencement_business = validity_start
                else:        
                    commencement_business = annual.employee_id.commencement_business
                    commencement_business = datetime.strptime(str(commencement_business),'%Y-%m-%d').date() 
                number_of_days = annual.parent_id.number_of_days
                date_now = datetime.today().date()
                statment_1 = (date_now - commencement_business).days + 1
                statment_2 = (validity_stop - validity_start).days + 1
                total =  number_of_days / 12 * (statment_1 / statment_2 * 12)
                float_round(total, precision_digits=2)
                total = float_round(total, precision_digits=2)
                _logger.info("------------------------")
                _logger.info(annual.employee_id.name)
                annual.number_of_days = total
                annual.number_of_days_display = total


                allocation_used_count = float_round(annual.employee_id.allocation_count - annual.employee_id.remaining_leaves, precision_digits=2)
                allocation_used_count_1 = "%g" % allocation_used_count
                _logger.info(allocation_used_count)
                _logger.info(allocation_used_count_1)
                _logger.info(annual.employee_id.allocation_count)
                _logger.info(annual.employee_id.remaining_leaves)




class CustomHrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"
    @api.model
    def _compute_total_allocation_used_1(self):
        print("_compute_total_allocation_used_1")
        print(self)
        for employee in self:
            employee.allocation_used_count = float_round(employee.allocation_count - employee.remaining_leaves, precision_digits=2)
            # employee.allocation_used_display = "%g" % employee.allocation_used_count
            employee.allocation_used_display_1 = "%g" % employee.allocation_used_count
    allocation_used_display_1 = fields.Char(compute='_compute_total_allocation_used_1')