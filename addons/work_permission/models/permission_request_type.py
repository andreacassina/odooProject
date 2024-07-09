from odoo import api,fields, models

class PermissionRequestType(models.Model):
    _name = "permission.request.type"
    _description = "Permission request type"
    _order = "id desc"

    name = fields.Char(required=True)
    description = fields.Text()

    _sql_constraints = [
        ('check_name', 'unique(name)',
         'The name must be unique.')
    ]

