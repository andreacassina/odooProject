from odoo import api,fields, models

class PermissionRequestType(models.Model):
    _name = "permission.request.type"
    _description = "Permission Request Type"
    _order = "name desc"
    _sql_constraints = [
        ('check_name', 'unique(name)', 'The name must be unique.')
    ]

    name = fields.Char(required=True)
    description = fields.Text()