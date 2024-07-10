from odoo import api,fields, models, exceptions
from datetime import datetime, timedelta

class PermissionRequest(models.Model):
    _name = 'permission.request'
    _description = 'Permission Request'
    _order = 'id desc'
    _sql_constraints = [
        ('check_duration_positive', 'CHECK(duration > 0)','Duration cannot be negative')
        ]

    title = fields.Char(compute = "_compute_title", readonly = True)
    description = fields.Text()  
    applicant = fields.Many2one("res.users", default = lambda self: self.env.user, required = True)
    request_type_id = fields.Many2one(
        "permission.request.type", string = "Request Type", required = True,
        default = lambda self: self.env['permission.request.type'].search([('name', '=', 'Unpaid')], limit=1)
    )
    active = fields.Boolean(default = True)
    state = fields.Selection(
        string='Permission State',
        selection=[('new', 'New'), ('pending', 'Pending'), ('accepted', 'Accepted'), ('refused', 'Refused')],
        help="Current Status of the permission request",
        required = True,
        default = 'new'
    )
    time_in = fields.Selection([ ('day', 'Day'), ('hour', 'Hour')], required = True, default = 'hour')
    datetime_from = fields.Datetime(default = lambda self: datetime.now(), required = True, string="To") # Included
    datetime_to = fields.Datetime(compute = "_compute_datetime_to", inverse = "_inverse_datetime_to", string="From") # Included
    duration = fields.Integer(required = True, default = 1)

    date_from = fields.Date(string="From (date only)")
    date_to = fields.Date(string="To (date only)")

    formatted_datetime_from = fields.Char(compute='_compute_formatted_datetimes', store=True)
    formatted_datetime_to = fields.Char(compute='_compute_formatted_datetimes', store=True)
    
    @api.depends('applicant', 'request_type_id', 'state', 'datetime_from', 'datetime_to')
    def _compute_title(self):
        for record in self:
            #record.title = "[" + record.state + "] " + record.applicant.name + ": " + record.request_type_id.name + " (" + (record.datetime_from + timedelta(hours=2)).strftime("%d/%m/%Y, %H:%M") + " - " + (record.datetime_to + timedelta(hours=2)).strftime("%d/%m/%Y, %H:%M") + ")"
            record.title = "[" + record.state + "] " + record.applicant.name + ": " + record.request_type_id.name + " (" + record.formatted_datetime_from + " - " + record.formatted_datetime_to + ")"

    @api.depends('datetime_from', 'duration')
    def _compute_datetime_to(self):
        #raise exceptions.UserError(datetime.now())
        for record in self:
            if record.time_in == 'day': # 1 giorno di ferie = stesso giorno + 8 ore (default)
                record.datetime_to = record.datetime_from + timedelta(days = record.duration - 1, hours = 8)
            else:
                record.datetime_to = record.datetime_from + timedelta(hours = record.duration)

    def _inverse_datetime_to(self):
        for record in self:
            if record.time_in == 'day':
                record.duration = ((record.datetime_to - record.datetime_from).days + 1) * 8
            else:
                record.duration = (record.datetime_to - record.datetime_from).seconds//3600

    @api.constrains('datetime_to', 'datetime_from')
    def _check_datetime_to(self):
        for record in self:
            if record.datetime_to <= record.datetime_from:
                raise exceptions.UserError("Invalid time range: datetime_to <= datetime_from")

    @api.onchange('time_in')
    def _onchange_time_in(self):
        self._compute_datetime_to()     

        
    @api.depends('datetime_from', 'datetime_to', 'time_in')
    def _compute_formatted_datetimes(self):
        for record in self:
            if record.time_in == 'hour':
                # record.formatted_datetime_from = fields.Datetime.to_string(record.datetime_from)
                # record.formatted_datetime_to = fields.Datetime.to_string(record.datetime_to)
                record.formatted_datetime_from = record.datetime_from.strftime("%Y-%m-%d %H:%M")
                record.formatted_datetime_to = record.datetime_to.strftime("%Y-%m-%d %H:%M")
            else:
                record.formatted_datetime_from = fields.Date.to_string(record.datetime_from.date())
                record.formatted_datetime_to = fields.Date.to_string(record.datetime_to.date())

    @api.onchange('time_in', 'datetime_from', 'datetime_to', 'date_from', 'date_to')
    def _onchange_dates(self):
        if self.time_in == 'hour':
            if self.date_from:
                self.datetime_from = fields.Datetime.to_datetime(self.date_from)
            if self.date_to:
                self.datetime_to = fields.Datetime.to_datetime(self.date_to)
        else:
            if self.datetime_from:
                self.date_from = self.datetime_from.date()
            if self.datetime_to:
                self.date_to = self.datetime_to.date()

    # Function for accept or refuse the permission request
    def permission_request_action_accept(self):
        for record in self:
            if record.state != 'accepted' and record.state != 'refused':
                record.state = 'accepted'
        return True
    

    def permission_request_action_refuse(self):
        for record in self:
            if record.state != 'accepted' and record.state != 'refused':
                record.state = 'refused'
        return True