import re
from datetime import datetime, timedelta
from odoo import models, api, fields, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import email_split
from pytz import timezone, UTC


class AttachMedicalCertificate(models.Model):
    _inherit = 'hr.leave.type'
    # certificate_required = fields.Binary("Date of commencement of business")
    certificate_required = fields.Boolean()
    

class UploadAttachMedicalCertificate(models.Model):
    _inherit = 'hr.leave'
    attach_certificate = fields.Binary(string="Attach Certificate")
