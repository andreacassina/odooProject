from odoo import api,fields, models

class PermissionRequestType(models.Model):
    _name = "permission.request.type"
    _description = "Permission request type"
    _order = "name desc"

    name = fields.Char(required=True)
    description = fields.Text()
    time_in = fields.Selection([ ('day', 'Day'), ('hour', 'Hour'), ('both', 'Day/Hour')])


    _sql_constraints = [
        ('check_name', 'unique(name)',
         'The name must be unique.')
    ]