import re
from datetime import datetime, timedelta
from odoo import models, api, fields, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import email_split
import logging
_logger = logging.getLogger(__name__)
from pytz import timezone, UTC


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    leave_approvals = fields.One2many('leave.validation.status',
                                      'holiday_status',
                                      string='Leave Validators',
                                      track_visibility='always', help="Leave approvals")

    multi_level_validation = fields.Boolean(string='Multiple Level Approval',
                                            related='holiday_status_id.multi_level_validation',
                                            help="If checked then multi-level approval is necessary") 
    
    is_approved_user_id = fields.Boolean(default=False, compute='_check_is_approved_user_id')  
    all_emails = fields.Text()
    approved_emails = fields.Text()
    notApproved_emails = fields.Text()
    def _check_is_approved_user_id(self):
        current_uid = self.env.uid
        self.is_approved_user_id= False
        for l2 in self.leave_approvals: 
            #for approval button
            if l2.validation_status != True:
                # direct manager
                if l2.validators_type == 'direct_manager' and self.employee_id.parent_id.id != False:
                    if self.employee_id.parent_id.user_id.id != False:
                        if self.employee_id.parent_id.user_id.id == current_uid:
                            self.is_approved_user_id= True
                            break
                # manager of manager(i will check it)
                if l2.validators_type == 'manager_of_manager' and self.employee_id.parent_id.id != False:
                    if self.employee_id.parent_id.parent_id.id != False: 
                        if self.employee_id.parent_id.parent_id.user_id.id != False:
                            if self.employee_id.parent_id.parent_id.user_id.id == current_uid:
                                self.is_approved_user_id= True
                                break            
                # position
                if  l2.validators_type == 'position':
                    employees = self.env['hr.employee'].sudo().search([('multi_job_id','in',l2.holiday_validators_position.id)])
                    if len(employees) > 0:
                        for employee in employees:
                            if employee.user_id.id == current_uid:
                                self.is_approved_user_id= True
                        break
                #user
                if  l2.validators_type == 'user':
                    if l2.holiday_validators_user.id == current_uid:
                        self.is_approved_user_id= True
                        break
                if not(l2.approval != True or (l2.approval == True and l2.validation_status == True)): 
                    break        
    is_refused_user_id = fields.Boolean(default=True)
    # is_refused_user_id = fields.Boolean(default=True, compute='_check_is_refused_user_id')
    # def _check_is_refused_user_id(self):
    #     current_uid = self.env.uid
    #     self.is_refused_user_id = False
    #     for l2 in self.leave_approvals: 
    #         # direct manager
    #         if l2.validators_type == 'direct_manager' and self.employee_id.parent_id.id != False:
    #             if self.employee_id.parent_id.user_id.id != False:
    #                 if self.employee_id.parent_id.user_id.id == current_uid:
    #                     self.is_refused_user_id= True
    #                     # break
    #         # position
    #         if  l2.validators_type == 'position':
    #             employees = self.env['hr.employee'].sudo().search([('multi_job_id','in',l2.holiday_validators_position.id)])
    #             if len(employees) > 0:
    #                 for employee in employees:
    #                     if employee.user_id.id == current_uid:
    #                         self.is_refused_user_id= True
    #                 # break
    #         #user
    #         if  l2.validators_type == 'user':
    #             if l2.holiday_validators_user.id == current_uid:
    #                 self.is_refused_user_id= True
    #                 # break
    #         if not(l2.approval != True or (l2.approval == True and l2.validation_status == True)): 
    #             break        
    @api.onchange('holiday_status_id','number_of_days')
    def add_validators(self):
        """ Update the tree view and add new validators
        when leave type is changed in leave request form """
        if self.validation_type == "multi":
            li = []
            all_emails = ""
            self.leave_approvals = [(5, 0, 0)]
            for l in self.holiday_status_id.leave_validators:
                _logger.info("-------------log-------------")
                _logger.info(float(l.exceptions))
                _logger.info(self.number_of_days)
                if l.exceptions == False or self.number_of_days > float(l.exceptions):
                    # direct manager
                    if l.validators_type == 'direct_manager' and self.employee_id.parent_id.id != False:
                        if self.employee_id.parent_id.user_id.id != False:
                            if all_emails != "":
                                if str(self.employee_id.parent_id.user_id.login) not in all_emails:
                                    all_emails = all_emails + "," +str(self.employee_id.parent_id.user_id.login)
                            else:
                                all_emails = str(self.employee_id.parent_id.user_id.login)

                    # manager of manager(i will check it)
                    if l.validators_type == 'manager_of_manager' and self.employee_id.parent_id.id != False:
                        if self.employee_id.parent_id.parent_id.id != False: 
                            if self.employee_id.parent_id.parent_id.user_id.id != False:
                                if all_emails != "":
                                    if str(self.employee_id.parent_id.parent_id.user_id.login) not in all_emails:
                                        all_emails = all_emails + "," +str(self.employee_id.parent_id.parent_id.user_id.login)
                                else:
                                    all_emails = str(self.employee_id.parent_id.parent_id.user_id.login)
                    # position
                    if  l.validators_type == 'position':
                        employees = self.env['hr.employee'].sudo().search([('multi_job_id','in',l.holiday_validators_position.id)])
                        if len(employees) > 0:
                            for employee in employees:
                                if all_emails != "":
                                    if str(employee.user_id.login) not in all_emails:
                                        all_emails = all_emails + "," +str(employee.user_id.login)
                                else:
                                    all_emails = str(employee.user_id.login)
                    #user
                    if  l.validators_type == 'user':
                        if all_emails != "":
                            if str(l.holiday_validators_user.login) not in all_emails:
                                all_emails = all_emails + ","+str(l.holiday_validators_user.login)
                        else:
                            all_emails = str(l.holiday_validators_user.login)
                li.append((0, 0, {
                    'validators_type': l.validators_type,
                    'holiday_validators_user': l.holiday_validators_user.id,
                    'holiday_validators_position': l.holiday_validators_position.id,
                    'approval': l.approval,
                    'exceptions':l.exceptions
                }))
            self.leave_approvals = li
            self.all_emails = all_emails

    def _get_approval_requests(self):
        """ Action for Approvals menu item to show approval
        requests assigned to current user """
        # Ahmed AlOsaili 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (10) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":1,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        # })
        # all_data = {}
        # all_data[0] = {}
        # all_data[0]['id'] = 199
        # all_data[0]['date'] = "2021-02-22"

        # all_data[1] = {}
        # all_data[1]['id'] = 195
        # all_data[1]['date'] = "2021-02-22"

        # all_data[2] = {}
        # all_data[2]['id'] = 197
        # all_data[2]['date'] = "2021-02-22"

        # all_data[3] = {}
        # all_data[3]['id'] = 193
        # all_data[3]['date'] = "2021-02-22"

        # all_data[4] = {}
        # all_data[4]['id'] = 192
        # all_data[4]['date'] = "2021-02-22"

        # all_data[5] = {}
        # all_data[5]['id'] = 196
        # all_data[5]['date'] = "2021-02-22"

        # all_data[6] = {}
        # all_data[6]['id'] = 194
        # all_data[6]['date'] = "2021-02-22"

        # all_data[7] = {}
        # all_data[7]['id'] = 191
        # all_data[7]['date'] = "2021-02-01"

        # all_data[8] = {}
        # all_data[8]['id'] = 205
        # all_data[8]['date'] = "2021-03-14"

        # all_data[9] = {}
        # all_data[9]['id'] = 206
        # all_data[9]['date'] = "2021-03-17"

        # all_data[10] = {}
        # all_data[10]['id'] = 207
        # all_data[10]['date'] = "2021-04-14"

        # all_data[11] = {}
        # all_data[11]['id'] = 201
        # all_data[11]['date'] = "2021-01-06"

        # all_data[12] = {}
        # all_data[12]['id'] = 202
        # all_data[12]['date'] = "2021-01-06"

        # all_data[13] = {}
        # all_data[13]['id'] = 202
        # all_data[13]['date'] = "2021-01-06"
        # for x in all_data :
        #     id = all_data[x]['id']
        #     date = all_data[x]['date']
        #     emp = self.env['hr.employee'].sudo().search([('id','=',id)])
        #     emp.commencement_business = date
        # self.env['hr.employee'].sudo().write({"id":1,"commencement_business":'2021-01-01'})
        # Abdulaziz Alegeiry
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":125,
        #     "number_of_days_display":9.75,
        #     "number_of_days":9.75,
        #     "state":'validate',
        #     "allocation_carry_forword" :True  
        # })
        # # Mahmoud Tash
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (10) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":120,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # # Mohammed Alaa Borgi
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (4.44) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":115,
        #     "number_of_days_display":4.44,
        #     "number_of_days":4.44,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # # Muzaffer Azam - Mohammed Muzaffer
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (7.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":103,
        #     "number_of_days_display":7.75,
        #     "number_of_days":7.75,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # # Mohamed Habib
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (10) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":100,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # # Shariful Islam
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":97,
        #     "number_of_days_display":21.88,
        #     "number_of_days":21.88,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # # Basel Alhamich
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":93,
        #     "number_of_days_display":2.7,
        #     "number_of_days":2.7,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # # Emad Abuzahra 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":7,
        #     "number_of_days_display":9.31,
        #     "number_of_days":9.31,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Mohammed Abdullah 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":89,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Mohammed Akram 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":146,
        #     "number_of_days_display":6.7,
        #     "number_of_days":6.7,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Ahmad Ibrahim Wadi Shahin 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":139,
        #     "number_of_days_display":5.49,
        #     "number_of_days":5.49,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Malek Jamal Rebhi Ahmad 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":145,
        #     "number_of_days_display":5.49,
        #     "number_of_days":5.49,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Basel Altamimi 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":144,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Ahmed Abosaleh 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":140,
        #     "number_of_days_display":1.76,
        #     "number_of_days":1.76,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Sultan Alhaqqas 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":149,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Elias Gabour  
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":151,
        #     "number_of_days_display":2.2,
        #     "number_of_days":2.2,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        #  Abdulrahman Altamimi 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":138,
        #     "number_of_days_display":-0.8,
        #     "number_of_days":-0.8,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        #  Tammam Madarati 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":153,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        #  Ahmed Elayyan 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":141,
        #     "number_of_days_display":-0.95,
        #     "number_of_days":-0.95,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        #  Qusai 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":158,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        #  Ramzi Madhi 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":161,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        #  Sonny Tesorero Tapia 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":155,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Eduard Nelson Akim 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":162,
        #     "number_of_days_display":10,
        #     "number_of_days":10,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Osama Alsuliman 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":163,
        #     "number_of_days_display":6.76,
        #     "number_of_days":6.76,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Moawia Jallad 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":166,
        #     "number_of_days_display":8.26,
        #     "number_of_days":8.26,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Jacinto Dugan Dimaun  
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":171,
        #     "number_of_days_display":8.26,
        #     "number_of_days":8.26,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Faris Badhris 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":172,
        #     "number_of_days_display":6.84,
        #     "number_of_days":6.84,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Ibrahim Alsebai 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":178,
        #     "number_of_days_display":3.62,
        #     "number_of_days":3.62,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Mohammed Lafeer 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":182,
        #     "number_of_days_display":5.48,
        #     "number_of_days":5.48,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Mohammed Hamood 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":176,
        #     "number_of_days_display":6.15,
        #     "number_of_days":6.15,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Rashed Aldawsari 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":174,
        #     "number_of_days_display":6.57,
        #     "number_of_days":6.57,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })
        # #  Fahad Alhamazani 
        # self.env['hr.leave.allocation'].sudo().create({
        #     "name":"Carry Forword from annual leave 2020 (9.75) days",
        #     "holiday_status_id":11,
        #     "allocation_type":"regular",
        #     "holiday_type":"employee",
        #     "employee_id":200,
        #     "number_of_days_display":3.62,
        #     "number_of_days":3.62,
        #     "state":'validate',
        #     "allocation_carry_forword" :True
        # })

        



        current_uid = self.env.uid
        hr_holidays = self.env['hr.leave'].sudo().search([('state','=','confirm'),('holiday_status_id.validation_type','=','multi')])
        li = []
        for l in hr_holidays:
            for l2 in l.leave_approvals:
                if l2.exceptions == False or l.number_of_days > float(l2.exceptions): 
                    # direct manager
                    if l2.validators_type == 'direct_manager' and l.employee_id.parent_id.id != False:
                        if l.employee_id.parent_id.user_id.id != False:
                            if l.employee_id.parent_id.user_id.id == current_uid:
                                li.append(l.id)

                    # manager of manager(i will check it)
                    if l2.validators_type == 'manager_of_manager' and l.employee_id.parent_id.id != False:
                        if l.employee_id.parent_id.parent_id.id != False: 
                            if l.employee_id.parent_id.parent_id.user_id.id != False:
                                if l.employee_id.parent_id.parent_id.user_id.id == current_uid:
                                    li.append(l.id)
                                
                    # position
                    if  l2.validators_type == 'position':
                        employee = self.env['hr.employee'].sudo().search([('multi_job_id','in',l2.holiday_validators_position.id),('user_id','=',current_uid)])
                        if len(employee) > 0:
                            li.append(l.id)
                    #user
                    if  l2.validators_type == 'user':
                        if l2.holiday_validators_user.id == current_uid:
                            li.append(l.id)
                    # if not(l2.approval != True or (l2.approval == True and l2.validation_status == True)): 
                    #     break                                 
        value = {
            'domain': str([('id', 'in', li)]),
            'view_mode': 'tree,form',
            'res_model': 'hr.leave',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'name': _('Approvals'),
            'res_id': self.id,
            'target': 'current',
            'create': False,
            'edit': False,
        }
        return value
    def action_approve(self):
        
        """ Chack if any pending tasks is added if so reassign the pending
        task else call approval """
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if self.multi_level_validation:
            if any(holiday.state != 'confirm' for holiday in self):
                raise UserError(_(
                    'Leave request must be confirmed ("To Approve") in order to approve it.'))
            ohrmspro_vacation_project = self.sudo().env['ir.module.module'].search(
                [('name', '=', 'ohrmspro_vacation_project')],
                limit=1).state
            if ohrmspro_vacation_project == 'installed':
                return self.env['hr.leave'].check_pending_task(self)
            else:
                return self.approval_check()
        else:
            rtn = super(HrLeave,self).action_approve()
            return rtn          
    def approval_check(self):
        """ Check all leave validators approved the leave request if approved
         change the current request stage to Approved"""   
        return {
                'type': 'ir.actions.act_window',
                'name': 'Reason for Approval',
                'res_model': 'create.leave.comment',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('multiApprovalTimeOff.view_create_leave_comment',False).id,
                'target': 'new',
        }
    def action_refuse(self):
        """ Refuse the leave request if the current user is in
        validators list """
        if self.multi_level_validation: 
            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Reason for Refused',
                    'res_model': 'create.refuse.comment',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('multiApprovalTimeOff.view_create_refuse_comment',False).id,
                    'target': 'new',
            }
        else:
            rtn = super(HrLeave,self).action_refuse()
            return rtn        
    def action_draft(self):
        """ Reset all validation status to false when leave request
        set to draft stage"""
        if self.multi_level_validation:
            for user in self.leave_approvals:
                user.validation_status = False
                user.validation_refused = False
        return super(HrLeave, self).action_draft()
    @api.model_create_multi
    def create(self,vals):
        rtn = super(HrLeave,self).create(vals)
        res_id = rtn.id
        for values in vals:
            holiday_status_id = values.get('holiday_status_id')
            employee_id = values.get('employee_id')
            request_date_from = values.get('request_date_from')
            request_date_to = values.get('request_date_to')
            number_of_days = values.get('number_of_days')
            all_emails = values.get('all_emails')
        hr_holidays = self.env['hr.leave.type'].sudo().search([('id','=',holiday_status_id)])
        if hr_holidays.validation_type == "multi":
            employee = self.env['hr.employee'].sudo().search([('id','=',employee_id)])
            message = ('<h4>Request approval to leave by %s<h4><br/>') % (employee.name)
            message += ('<p style="font-size: 12px;">From %s</p><br/>') % (request_date_from)
            message += ('<p style="font-size: 12px;">To %s</p><br/>') % (request_date_to)
            message += ('<p style="font-size: 12px;">Duration: %s</p><br/>') % (number_of_days)
            body_html = self.create_body_for_email(message,res_id)
            email_html = self.create_header_footer_for_email(holiday_status_id,employee_id,body_html)
              
            value = {
                'subject': 'Approval of the leave',
                'body_html': email_html,
                'email_to': all_emails,
                'email_cc': '',
                'auto_delete': False,
                'email_from': 'axs-sa.com',
            }
            mail_id = self.env['mail.mail'].sudo().create(value)
            mail_id.sudo().send()
        return rtn          

    def create_body_for_email(self,message,res_id):
        body_html = ''
        body_html +='<tr>'
        body_html +=    '<td align="center" style="min-width: 590px;">'
        body_html +=        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
        body_html +=            '<tr>'
        body_html +=                '<td valign="top" style="font-size: 13px;">'
        body_html +=                    '<p style="margin: 0px;font-size: 14px;">'
        body_html +=                        message
        body_html +=                    '</p>'
        body_html +=                    '<p style="margin-top: 24px; margin-bottom: 16px;">'
        body_html +=                        ('<a href="/mail/view?model=hr.leave&amp;res_id=%s" style="background-color:#875A7B; padding: 10px; text-decoration: none; color: #fff; border-radius: 5px;">') % (res_id)
        body_html +=                            'View Leave'
        body_html +=                        '</a>'
        body_html +=                    '</p>'
        body_html +=                    'Thanks,<br/>'
        body_html +=                '</td>'
        body_html +=            '</tr>'
        body_html +=            '<tr>'
        body_html +=                '<td style="text-align:center;">'
        body_html +=                    '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
        body_html +=                '</td>'
        body_html +=            '</tr>'
        body_html +=        '</table>'
        body_html +=    '</td>'
        body_html +='</tr>'
        return body_html
    def create_header_footer_for_email(self,holiday_status_id,employee_id,body_html):
        hr_holidays = self.env['hr.leave.type'].sudo().search([('id','=',holiday_status_id)])
        employee = self.env['hr.employee'].sudo().search([('id','=',employee_id)])
        leave_type = hr_holidays.name
        company_id = employee.company_id.id
        header = ''
        header += '<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">'                      
        header +=   '<tr>'
        header +=       '<td align="center">' 
        header +=           '<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
        header +=               '<tbody>'

        header +=                   '<tr>'
        header +=                       '<td align="center" style="min-width: 590px;">'
        header +=                           '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
        header +=                               '<tr><td valign="middle">'
        header +=                                   '<span style="font-size: 10px;">Leave Approval</span><br/>'
        header +=                                   '<span style="font-size: 20px; font-weight: bold;">'
        header +=                                       leave_type
        header +=                                   '</span>'
        header +=                               '</td><td valign="middle" align="right">'
        header +=                                  ('<img src="/logo.png?company=%s" style="padding: 0px; margin: 0px; height: auto; width: 80px;" alt=""/>') % (str(company_id))
        header +=                               '</td></tr>'
        header +=                               '<tr><td colspan="2" style="text-align:center;">'
        header +=                                   '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
        header +=                               '</td></tr>'
        header +=                           '</table>'
        header +=                       '</td>'
        header +=                   '</tr>'
        header +=                   body_html
        header +=                   '<tr>' 
        header +=                       '<td align="center" style="min-width: 590px;">' 
        header +=                           '<table border="0" cellpadding="0" cellspacing="0" width="622px" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 24px; border-collapse:separate;">'
        header +=                               '<tr><td valign="middle" align="left">'
        header +=                                   str(employee.company_id.name)
        header +=                               '</td></tr>'
        header +=                               '<tr><td valign="middle" align="left" style="opacity: 0.7;">'
        header +=                                   str(employee.company_id.phone)                
        if employee.company_id.email:
            header += ('<a href="mailto:%s" style="text-decoration:none; color: #454748;">%s</a>') % (str(employee.company_id.email),str(employee.company_id.email))
        if employee.company_id.website:
            header += ('<a href="%s" style="text-decoration:none; color: #454748;">') % (str(employee.company_id.website))    
        header +=                               '</td></tr>'
        header +=                           '</table>'
        header +=                       '</td>'
        header +=                   '</tr>'

        header +=               '</tbody>'
        header +=           '</table>'
        header +=       '</td>'
        header +=     '</tr>'
        header +=     '<tr>'
        header +=       '<td align="center" style="min-width: 590px;">'
        header +=           '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">'
        header +=               '<tr><td style="text-align: center; font-size: 13px;">'
        header +=                   "Powered by "+ ('<a target="_blank" href="%s" style="color: #875A7B;">%s</a>') % (str(employee.company_id.website),str(employee.company_id.name)) 
        header +=               '</td></tr>'
        header +=           '</table>'
        header +=       '</td>'
        header +=     '</tr>'
        header +=   '</table>'
        return header
