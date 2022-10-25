from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
import calendar
from . import common
from datetime import time
import math
from pytz import timezone
import pytz

class HrEmployeeInherit(models.Model):
    _inherit = "hr.employee"
    
    test_field = fields.Char("Total time")
    total_leaves = fields.Float(string="Total Leaves", compute="_compute_total_leaves")
    contract_type_id = fields.Many2one('hr.contract.type', related='contract_id.contract_type_id', string="Contract Type", store=True)

    def action_employee_test(self):
        mail_template = self.env.ref("KLTN.mail_template_employee_test")
        mail_template.sudo().send_mail(self.id, force_send=True)

    def get_detail_employee(self):
        data = {}
        date_from = datetime(datetime.now().year, datetime.now().month, 1)
        date_to = datetime(datetime.now().year, datetime.now().month, calendar.monthrange(
            datetime.now().year, datetime.now().month)[1])


        attendance_data = self.env['hr.attendance'].search([
            ("employee_id", "=", self.env.user.employee_id.id),
            '&',
                ("check_in", ">=", date_from),
                ("check_in", "<=", date_to)
        ])

        attendance_request_data = self.env['hr.attendance.request'].search([
            ("employee_id", "=", self.env.user.employee_id.id),
            '&',
                ("date_from", ">=", date_from),
                ("date_from", "<=", date_to)
        ])

        leave_data = self.env['hr.leave'].search([
            ("employee_id", "=", self.env.user.employee_id.id),
            '&',
                ("date_from", ">=", date_from),
                ("date_from", "<=", date_to)
        ])

        overtime_data = self.env['hr.overtime.request'].search([
            ("employee_id", "=", self.env.user.employee_id.id),
            '&',
                ("date", ">=", date_from),
                ("date", "<=", date_to)
        ])

        number_of_hour_overtime = 0
        for data in overtime_data:
            number_of_hour_overtime += data.number_of_hours
        
        data = {
            "attendance_count": len(attendance_data),
            "attendance_request_count": len(attendance_request_data),
            "leave_count": len(leave_data),
            "overtime_count": len(overtime_data),
            "overtime_hour_count": number_of_hour_overtime
        }

    def _compute_total_leaves(self):
        for rec in self:
            leave_type_for_compute = rec.env['ir.config_parameter'].sudo().get_param('leave_type_for_compute')
            if leave_type_for_compute:
                leave_type_for_compute = leave_type_for_compute.split(',')
            total_leaves = rec.env['hr.leave.allocation.inherit'].search([
                ('employee_id', '=', rec.id),
                ('state', '=', 'validate'),
                ('leave_type_code', 'in', leave_type_for_compute),
            ])

            total = 0
            for data in total_leaves:
                total += data.number_of_day
            rec.total_leaves = total

    def _get_employee_resource_calendar(self, date_from, date_to, is_half=False):
        # TODO check if date_from and date_to is in attendance_ids
        # local = pytz.timezone(str(self.env.user.tz))
        local = pytz.timezone(self.env.context.get('tz') or self.env.user.tz)
        print("**************", local)
        if date_from and date_to:
            list_data = []
            for dt in common.daterange(date_from, date_to):
                for attendance in self.contract_id.resource_calendar_id.attendance_ids:
                    if int(attendance.dayofweek) == int(dt.weekday()):
                        check_in = datetime.combine(dt, time(hour=math.floor(attendance.hour_from), minute=int(math.modf(attendance.hour_from)[0]*60)))
                        check_out = datetime.combine(dt, time(hour=math.floor(attendance.hour_to), minute=int(math.modf(attendance.hour_to)[0]*60)))
                        value = {
                            'employee_id': self.id,
                            'check_in': datetime(check_in, tzinfo=pytz.UTC).astimezone(timezone('utc')),
                            'check_out': datetime(check_out, tzinfo=pytz.UTC).astimezone(timezone(local))
                        }
                        list_data.append(value)
            return list_data
        if date_from and is_half:
            list_data = []
            for attendance in self.contract_id.resource_calendar_id.attendance_ids:
                if int(attendance.dayofweek) == int(date_from.weekday()):
                    check_in_data = datetime.combine(date_from, time(hour=math.floor(attendance.hour_from), minute=int(math.modf(attendance.hour_from)[0]*60)))
                    check_out_data = datetime.combine(date_from, time(hour=math.floor(attendance.hour_to), minute=int(math.modf(attendance.hour_to)[0]*60)))

                    # check_in = pytz.utc.localize(check_in_data).astimezone('utc').replace(tzinfo=None)
                    # check_out = pytz.utc.localize(check_out_data).astimezone('utc').replace(tzinfo=None)

                    check_in_data = check_in_data - timedelta(hours=7)
                    check_out_data = check_out_data - timedelta(hours=7)
                    value = {
                        'employee_id': self.id,
                        'check_in': check_in_data,
                        'check_out': check_out_data
                    }
                    list_data.append(value)
            return list_data

    
    



    

    


    


