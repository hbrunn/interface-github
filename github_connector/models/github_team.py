# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today: Odoo Community Association (OCA)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class GithubTeam(models.Model):
    _name = 'github.team'
    _inherit = ['abstract.github.model']
    _order = 'name'

    _github_type = 'team'
    _github_login_field = 'slug'

    # Column Section
    organization_id = fields.Many2one(
        comodel_name='github.organization', string='Organization',
        required=True, index=True, readonly=True, ondelete='cascade')

    name = fields.Char(
        string='Name', index=True, required=True, readonly=True)

    membership_ids = fields.One2many(
        string='Members', comodel_name='github.team.membership',
        inverse_name='team_id', readonly=True)

    membership_qty = fields.Integer(
        string='Members Quantity', compute='_compute_membership_qty',
        store=True)

    description = fields.Char(string='Description', readonly=True)

    complete_name = fields.Char(
        string='Complete Name', readonly=True,
        compute='_compute_complete_name', store=True)

    github_url = fields.Char(
        string='Github URL', compute='_compute_github_url', readonly=True)

    # Compute Section
    @api.multi
    @api.depends('github_login', 'organization_id.github_login')
    def _compute_github_url(self):
        for team in self:
            team.github_url = "https://github.com/orgs/{organization_name}/"\
                "teams/{team_name}".format(
                    organization_name=team.organization_id.github_login,
                    team_name=team.github_login)

    @api.multi
    @api.depends('name', 'organization_id.github_login')
    def _compute_complete_name(self):
        for team in self:
            team.complete_name =\
                team.organization_id.github_login + '/' + team.github_login

    @api.multi
    @api.depends('membership_ids')
    def _compute_membership_qty(self):
        for team in self:
            team.membership_qty = len(team.membership_ids)

    # Overloadable Section
    def get_odoo_data_from_github(self, data):
        res = super(GithubTeam, self).get_odoo_data_from_github(data)
        res.update({
            'name': data['name'],
            'description': data['description'],
        })
        return res

    @api.multi
    def full_update(self):
        self.button_sync_member()

    # Action Section
    @api.multi
    def button_sync_member(self):
        partner_obj = self.env['res.partner']
        connector_member = self.get_github_for('team_members_member')
        connector_maintainer = self.get_github_for('team_members_maintainer')
        for team in self:
            membership_data = []
            for data in connector_member.list([team.github_id_external]):
                partner = partner_obj.get_from_id_or_create(data)
                membership_data.append(
                    {'partner_id': partner.id, 'role': 'member'})
            for data in connector_maintainer.list([team.github_id_external]):
                partner = partner_obj.get_from_id_or_create(data)
                membership_data.append(
                    {'partner_id': partner.id, 'role': 'maintainer'})
            team.membership_ids = [
                (2, x.id, False) for x in team.membership_ids]
            team.membership_ids = [(0, False, x) for x in membership_data]
