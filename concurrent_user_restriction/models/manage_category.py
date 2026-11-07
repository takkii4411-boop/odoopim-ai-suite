from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.http import request

class PimCategory(models.Model):
    _inherit = 'pim.category'

    editing = fields.Boolean(default=False)
    edit_session_name = fields.Char()
    lock_time = fields.Datetime()
    edit_session_id = fields.Many2one('session.info')

    def can_edit_session(self):
        if not self.env.user.has_group('pim_ext.group_admin_user') or not self.id:
            return 2
        if self.edit_session_name == request.session.sid:
            return 1
        else:
            return 0

    def check_lock(self):
        print("self.edit_session_name", self.edit_session_name, self.edit_session_id)
        if self.env.user.has_group('pim_ext.group_admin_user'):
            time_now = datetime.now()
            time_diff = (time_now - self.lock_time).total_seconds() / 60
            self_session = request.session.sid
            print(time_diff)
            if time_diff >= 2:
                sessions = self.get_editing_session(self_session)
                if len(sessions) > 1 and self.edit_session_id.session_id == self_session:
                    self.edit_session_name = False
                    self.edit_session_id.last_access_time = datetime.now()
                    return 2
                if self.edit_session_name == False and sessions[0].session_id == self_session:
                    return 1
                if time_diff >= 1 and self.edit_session_id.session_id != self_session:
                    self.edit_session_name = False
                    self.edit_session_id.last_access_time = False
                    self.edit_session_id.active_state  = False
                    return 1
            sessions = self.get_editing_session(self_session)
            if self.edit_session_name == False and sessions[0].session_id == self_session:
                return 1

    def clear_edit_session(self):
        print("clear edit session", self.edit_session_name)
        if self.env.user.has_group('pim_ext.group_admin_user'):
            self_session = request.session.sid
            session_details = self.env['session.info'].search(
                [('session_id', '=', self_session), ('category_id', '=', self.id)])
            if self.edit_session_name == self_session:
                self.edit_session_id = False
                self.edit_session_name = False
                self.editing = False
                session_details.active_state = False
            session_details.active_state = False
            session_details.last_access_time = datetime.now()

    def save_session(self, self_session):
        session_details = self.env['session.info'].search(
            [('session_id', '=', self_session), ('category_id', '=', self.id)])
        time_now = datetime.now()
        time_margin = time_now - timedelta(seconds=10)
        if not session_details:
            self.env['session.info'].create({'session_id': self_session,
                                             'category_id': self.id,
                                             'last_access_time': datetime.now(),
                                             'active_state': True
                                             # 'last_visit_time':datetime.now(),
                                             })
        # if the session record exist, and it's state is not active, we update last_access_time
        if not session_details.active_state:
            # session_details.last_visit_time = time_now
            session_details.last_access_time = time_now
        session_details.active_state = True

    def get_editing_session(self, session):
        sessions = self.env['session.info'].search([('category_id', '=', self.id), ('active_state', '=', True)],
                                                   order='last_access_time asc')
        return sessions

    def disable_editing(self):
        if self.id:
            print("disable editing", request.session.sid)
            if self.env.user.has_group('pim_ext.group_admin_user'):
                self_session = request.session.sid
                self.save_session(self_session)
                sessions = self.get_editing_session(self_session)
                if self_session == sessions[0].session_id:
                    self.edit_session_id = sessions[0]
                    self.edit_session_name = self.edit_session_id.session_id
                    self.editing = True
                    self.lock_time = datetime.now()

    @api.onchange('name', 'code', 'active', 'parent_id', 'complete_name')
    def edit_mode(self):
        if self.env.user.has_group('pim_ext.group_admin_user'):
            if self.editing:
                if not self.edit_session_name:
                    raise ValidationError("Another user is editing. Please reload and try again.")
                elif self.editing and self.edit_session_name != request.session.sid:
                    raise ValidationError("Another user is editing. Please reload and try again.")
        else:
            raise ValidationError("You dont have the right to edit Family.")