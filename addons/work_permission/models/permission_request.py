from odoo import api,fields, models, exceptions
from datetime import datetime, timedelta
import math

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
    datetime_to = fields.Datetime(compute = "_compute_datetime_to", inverse = "_inverse_datetime_to", string="To") # Included
    duration = fields.Integer(required = True, default = 1)

    sort_order = fields.Integer(compute='_compute_sort_order', store=True)
    
    ###############################################################################################################
    ############################################### COMPUTED FIELDS ###############################################
    ###############################################################################################################

    @api.depends('applicant', 'request_type_id', 'state', 'datetime_from', 'datetime_to')
    def _compute_title(self):
        for record in self:
            record.title = "[" + record.state + "] " + record.applicant.name + ": " + record.request_type_id.name + " ("
            if record.time_in == 'hour':
                record.title += record.datetime_from.strftime("%d/%m/%Y %H:%M") + " - " + record.datetime_to.strftime("%d/%m/%Y %H:%M") + ")"
            else:
                record.title += record.datetime_from.strftime("%d/%m/%Y") + " - " + record.datetime_to.strftime("%d/%m/%Y") + ")"

    @api.depends('datetime_from', 'duration', 'time_in')
    def _compute_datetime_to(self):
        for record in self:
            if record.time_in == 'day':
                #record.datetime_from -= timedelta(hours=record.datetime_from.hour+2, minutes=record.datetime_from.minute, seconds=record.datetime_from.second, microseconds=record.datetime_from.microsecond - 100)
                record.datetime_from -= timedelta(days=-1, hours=record.datetime_from.hour+2, minutes=record.datetime_from.minute, seconds=record.datetime_from.second)
                record.datetime_to = record.datetime_from + timedelta(days = record.duration - 1, hours=23, minutes = 59)
                #record.datetime_to = record.datetime_from + timedelta(days = record.duration - 1)
            else: # record.time_in == 'hour'
                record.datetime_from -= timedelta(seconds=record.datetime_from.second)
                record.datetime_to = record.datetime_from + timedelta(hours = record.duration)

    def _inverse_datetime_to(self):
        for record in self:
            if record.time_in == 'day':
                record.datetime_to -= timedelta(hours=record.datetime_to.hour-21, minutes=record.datetime_to.minute-59, seconds=record.datetime_to.second)
                record.duration = (record.datetime_to - record.datetime_from).days + 1   
            else:
                if(record.datetime_from + timedelta(days=1) < record.datetime_to):
                    raise exceptions.UserError("Invalid duration: You are asking more than 24 hours permission: Use a Dayly Permission")
                record.duration = math.ceil((record.datetime_to - record.datetime_from).seconds/3600)
    
    @api.depends('state', 'datetime_from')
    def _compute_sort_order(self):
        for record in self:
            if record.state == 'new':
                record.sort_order = 0
            else:
                record.sort_order = 1

                

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