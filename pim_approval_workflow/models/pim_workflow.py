from odoo import models, fields, api

class PimWorkflow(models.Model):
    _name = 'pim.workflow'
    _description = 'PIM Workflow'
    _check_company_auto = True

    name = fields.Char(string='Workflow Name', required=True)
    description = fields.Char(string='Workflow Description')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string='Status', default='draft')
    stage_ids = fields.One2many(
        'pim.workflow.stage',
        'workflow_id',
        string='Stages',
        copy=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True
    )

    category_ids = fields.Many2many(
        'product.category',
        string='Product Categories',
        help="Workflow applies to products in these categories.",
    )
    family_ids = fields.Many2many(
        'family.attribute',
        string='Product Families',
        help="Workflow applies to products in these families.",
        domain="[('company_id', '=', company_id)]"
    )
    attribute_ids = fields.Many2many(
        'product.attribute',
        string='Attributes to Check',
        help="Specific attributes that must be validated or are relevant for this workflow.",
        domain="[('company_id', '=', company_id)]"
    )
    attribute_group_ids = fields.Many2many(
        'attribute.group',
        string='Attribute Groups',
        help="Attribute groups that must be complete or reviewed in this workflow.",
        domain="[('company_id', '=', company_id)]"
    )
    product_ids = fields.One2many(
        'product.template', 'pim_workflow_id',
        string='Matching Products',
        compute='_compute_matching_products',
        readonly=True,
        help="Products that match the selected categories and/or families."
    )

    @api.depends('category_ids', 'family_ids', 'attribute_ids', 'attribute_group_ids', 'company_id')
    def _compute_matching_products(self):
        Product = self.env['product.template']

        for workflow in self:
            domain = []

            if workflow.category_ids:
                domain.append(('categ_id', 'in', workflow.category_ids.ids))

            if workflow.family_ids:
                domain.append(('family_id', 'in', workflow.family_ids.ids))

            if workflow.attribute_ids:
                domain.append(
                    ('attribute_line_ids.attribute_id', 'in', workflow.attribute_ids.ids)
                )

            if workflow.attribute_group_ids:
                families = self.env['family.attribute'].search([
                    ('exist_group_ids', 'in', workflow.attribute_group_ids.ids),
                    ('company_id', '=', workflow.company_id.id)
                ])
                domain.append(('family_id', 'in', families.ids))

            if not domain:
                workflow.product_ids = False
                continue

            workflow.product_ids = Product.search(domain)


class PimWorkflowStage(models.Model):
    _name = 'pim.workflow.stage'
    _description = 'PIM Workflow Stage'
    _order = 'sequence, id'
    _check_company_auto = True

    workflow_id = fields.Many2one('pim.workflow', string='Workflow', required=True, ondelete='cascade')
    name = fields.Char(string='Stage Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    group_id = fields.Many2one(
        'res.groups',
        string='Assigned Group/Role',
        required=True,
    )
    user_ids = fields.Many2many(
        'res.users',
        string='Assigned Users',
        domain="[('groups_id', 'in', group_id), ('company_ids', 'in', company_id)]",
        help="Select one or more users from the assigned group to handle this stage."
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True
    )