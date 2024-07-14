from odoo import api,fields, models, exceptions
from datetime import datetime, timedelta
import pytz

class PermissionRequest(models.Model):
    _name = 'permission.request'
    _description = 'Permission Request'
    _order = 'sort_order asc, datetime_from desc'
    _sql_constraints = [
        ('check_duration_positive', 'CHECK(duration > 0)','Duration must be positive')
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
    datetime_from = fields.Datetime(default = lambda self: datetime.now(), required = True, string="From") # Included
    datetime_to = fields.Datetime(compute = "_compute_datetime_to", string="To") # Included
    duration = fields.Integer(required = True, default = 1)

    sort_order = fields.Integer(compute='_compute_sort_order', store=True)
    create_date = fields.Datetime('Creation Date', readonly=True, default = lambda self: datetime.now())

    ###############################################################################################################
    ############################################### COMPUTED FIELDS ###############################################
    ###############################################################################################################

    @api.depends('applicant', 'request_type_id', 'state', 'create_date')
    def _compute_title(self):
        utc_tz = pytz.utc
        rome_tz = pytz.timezone('Europe/Rome')
        now_utc = datetime.now(utc_tz)
        now_rome = now_utc.astimezone(rome_tz)
        time_diff = now_rome.utcoffset() - now_utc.utcoffset()
        for record in self:
            record.title = "[" + record.state + "] " + record.applicant.name + ": " + record.request_type_id.name + " (" + (record.create_date+time_diff).strftime("%d/%m/%Y %H:%M:%S") + ")"

    @api.depends('datetime_from', 'duration', 'time_in')
    def _compute_datetime_to(self):
        for record in self:
            if record.time_in == 'day':
                record.datetime_from -= timedelta(days=-1, hours=record.datetime_from.hour+2, minutes=record.datetime_from.minute, seconds=record.datetime_from.second)
                record.datetime_to = record.datetime_from + timedelta(days = record.duration - 1, hours=23, minutes = 59)
            else: # record.time_in == 'hour'
                record.datetime_from -= timedelta(seconds=record.datetime_from.second)
                record.datetime_to = record.datetime_from + timedelta(hours = record.duration)
    
    @api.depends('state')
    def _compute_sort_order(self):
        for record in self:
            if record.state == 'new':
                record.sort_order = 0
            elif record.state == 'pending':
                record.sort_order = 1
            elif record.state == 'accepted':
                record.sort_order = 2
            else:
                record.sort_order = 3

    @api.model
    def check_and_update_state(self):

        all_records = self.search([])

        for record in all_records:
            if record.create_date != None:
                #if record.create_date < (datetime.now() - timedelta(seconds=30)):
                if record.create_date < (datetime.now() - timedelta(days=3)):
                    if record.state == 'new' or record.state == 'pending':
                        record.state = 'refused'
                """else:
                    record.state = 'accepted'"""

    ###############################################################################################################
    ############################################# ONCHANGE FUNCTIONS ##############################################
    ###############################################################################################################

    ###############################################################################################################
    ############################################ COSTRAINTS FUNCTIONS #############################################
    ###############################################################################################################

    @api.constrains('datetime_to', 'datetime_from')
    def _check_datetime_to(self):
        for record in self:
            if record.datetime_to <= record.datetime_from:
                raise exceptions.UserError("Invalid time range: datetime_to <= datetime_from")

    @api.constrains('duration')
    def _check_datetime_to(self):
        for record in self:
            if record.time_in == 'hour' and record.duration >= 24:
                raise exceptions.UserError("Invalid duration: You are asking more than 24 hours permission: Use a Dayly Permission")

    ##############################################################################################################
    ############################################### VIEW FUNCTIONS ###############################################
    ##############################################################################################################

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

    def permission_request_action_read(self):
        for record in self:
            if record.state != 'accepted' and record.state != 'refused':
                record.state = 'pending'
        return True

    def _get_today_date(self):
        return datime.now()