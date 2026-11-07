# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ImageAttributeType(models.Model):
    _name = 'image.attribute.type'
    _description = 'Image/File Attribute Types'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        help='Display name (e.g., JPEG, PNG, PDF)'
    )
    extension = fields.Char(
        string='Extension',
        required=True,
        help='File extension without dot (e.g., jpg, png, pdf)'
    )

    _sql_constraints = [
        ('extension_unique', 'unique(extension)', 'Extension must be unique!')
    ]

    @api.constrains('extension')
    def _check_extension_format(self):
        for rec in self:
            if not rec.extension:
                continue

            clean_ext = rec.extension.replace('.', '').lower()

            if not re.match(r'^[a-z0-9]+$', clean_ext):
                raise ValidationError(_(
                    'Extension must contain only letters and numbers '
                    'without dots or special characters.'
                ))

            if rec.extension != clean_ext:
                rec.extension = clean_ext

    def name_get(self):
        return [(rec.id, f"{rec.name} (.{rec.extension})") for rec in self]
