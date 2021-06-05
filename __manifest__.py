# -*- coding: utf-8 -*-

{
    'name': 'Multi Approval Time Off',
    'version': '13.0',
    'summary': """Multi Approval Time Off""",
    'category': 'Generic Modules/Human Resources',
    'depends': ['base_setup', 'hr_holidays'],
    'data': [
        'wizards/create_leave_comment.xml',
        'wizards/create_refuse_comment.xml',
        'views/leave_request.xml',
        # 'views/hr_employee.xml',
        'data/mail_template.xml',
        'data/cron.xml',
        'security/ir.model.access.csv',
        'security/security.xml'
    ],
}
