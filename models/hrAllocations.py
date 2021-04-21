import re
from datetime import datetime,date, timedelta
from odoo import models, api, fields, _
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
                # number_of_days = annual.parent_id.number_of_days
                number_of_days = 22
                date_now = date(2021, 4, 15)
                # statment_1 = (validity_stop - commencement_business).days
                statment_1 = (date_now - commencement_business).days
                statment_2 = (validity_stop - validity_start).days + 1
                total =  number_of_days / 12 * (statment_1 / statment_2 * 12)
                total = round(total,2)
                _logger.info("------------------------")
                _logger.info(annual.employee_id.name)
                _logger.info(commencement_business)
                _logger.info(annual_leave_type.name)
                _logger.info(annual_leave_type.validity_start)
                _logger.info(validity_stop)
                _logger.info(statment_1)
                _logger.info(statment_2)
                _logger.info(number_of_days)
                _logger.info(round(total,2))
                _logger.info("------------------------")
            

    # @api.model
    # def getLeaveDate(commencement_business,validity_start,validity_stop,number_of_days):
    #     commencement_business = datetime.strptime(commencement_business,'%Y-%m-%d').date()
    #     statment_1 = (validity_stop - commencement_business).days
    #     statment_2 = (validity_stop - validity_start).days  
    #     _logger.info(commencement_business)
    #     _logger.info(validity_stop)
    #     _logger.info(validity_start)
    #     _logger.info(statment_1)
    #     _logger.info(statment_2)
    #     if commencement_business <= validity_start:
    #         return number_of_days
    #     else:     
    #         return round(((statment_1 / statment_2) * number_of_days),1)

    # @api.model
    # def create(self,vals):
    #     try: 
    #         rtn = super(HrEmployee,self).create(vals)  
    #         _logger.info("---------------------------")
    #         commencement_business = vals['commencement_business']
    #         department_id = vals['department_id']
    #         annual_leave_type = self.env['hr.leave.type'].sudo().search(['&',('finished_carry_froword','=',False),'|',('validity_stop','>=',commencement_business),'&',('validity_start','=',False),('validity_stop','=',False)])
    #         for annual in annual_leave_type:
    #             _logger.info(annual.name)
    #             annual_leave_allocation = self.env['hr.leave.allocation'].sudo().search([('holiday_status_id','=',annual.id),('state','=','validate')])
    #             # for only days and half day 
    #             for allocation in annual_leave_allocation:
    #                 all_number_of_days = allocation.number_of_days
    #                 validity_stop = annual.validity_stop
    #                 validity_start = annual.validity_start
    #                 # By Company
    #                 if allocation.holiday_type == "company":
    #                     _logger.info("By Company")
    #                     if vals['company_id'] != False:
    #                         if allocation.mode_company_id.id == vals['company_id']:
    #                             number_of_days = self.pool.get("hr.employee").getLeaveDate(commencement_business,validity_start,validity_stop,all_number_of_days)
    #                             _logger.info(number_of_days) 
    #                             self.env['hr.leave.allocation'].sudo().create({
    #                                 "name":allocation.name,
    #                                 "holiday_status_id":allocation.holiday_status_id.id,
    #                                 "allocation_type":allocation.allocation_type,
    #                                 "nextcall":allocation.nextcall,
    #                                 "number_per_interval":allocation.number_per_interval,
    #                                 "unit_per_interval":allocation.unit_per_interval,
    #                                 "interval_number":allocation.interval_number,
    #                                 "interval_unit":allocation.interval_unit,
    #                                 "holiday_type":"employee",
    #                                 "employee_id":rtn.id,
    #                                 "number_of_days_display":number_of_days,
    #                                 "number_of_days":number_of_days,
    #                                 "state":'validate',
    #                             })
                    # elif allocation.holiday_type == "department":
                    #     _logger.info("By Department")
                    #     if department_id != False:
                    #         if allocation.department_id.id == department_id:
                    #             number_of_days = self.pool.get("hr.employee").getLeaveDate(commencement_business,validity_start,validity_stop,all_number_of_days)
                    #             _logger.info(number_of_days) 
                    #             self.env['hr.leave.allocation'].sudo().create({
                    #                 "name":allocation.name,
                    #                 "holiday_status_id":allocation.holiday_status_id.id,
                    #                 "allocation_type":allocation.allocation_type,
                    #                 "nextcall":allocation.nextcall,
                    #                 "number_per_interval":allocation.number_per_interval,
                    #                 "unit_per_interval":allocation.unit_per_interval,
                    #                 "interval_number":allocation.interval_number,
                    #                 "interval_unit":allocation.interval_unit,
                    #                 "holiday_type":"employee",
                    #                 "employee_id":rtn.id,
                    #                 "number_of_days_display":number_of_days,
                    #                 "number_of_days":number_of_days,
                    #                 "state":'validate',
                    #             })
                    # elif allocation.holiday_type == "category":  



                                     
        # except Exception as inst:
        #     _logger.info("An exception occurred") 
        #     _logger.info(inst)     
                                         
        # return rtn 

