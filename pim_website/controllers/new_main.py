from odoo import http, fields
from odoo.http import request
from odoo.tools import float_round
import re
try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None

class PXMShopController(http.Controller):

    @http.route([
        '/pxm/shop/<string:slug>-<int:product_id>',
        '/pxm/product/<int:product_id>'
    ], type='http', auth='public', website=True)
    def pxm_product_detail(self, product_id, slug=None, **kw):

        Product = request.env['product.template'].sudo()
        product = Product.browse(product_id)

        if not product.exists():
            return request.not_found()

        website = request.env['website'].get_current_website()

        # ============================================================
        # IMAGE GALLERY (PRIMARY FIRST)
        # ============================================================
        image_gallery = []
        images = product.image_ids.filtered(lambda i: i.image_1920)

        primary_img = images.filtered(lambda i: i.is_primary)[:1]

        if primary_img:
            image_gallery.append(primary_img.image_1920.decode())
            for img in images.filtered(lambda i: i.id != primary_img.id).sorted('sequence'):
                image_gallery.append(img.image_1920.decode())
        else:
            for img in images.sorted('sequence'):
                image_gallery.append(img.image_1920.decode())

        if not image_gallery and product.image_1920:
            image_gallery.append(product.image_1920.decode())

        # ============================================================
        # DYNAMIC ATTRIBUTE DEFINITIONS
        # ============================================================
        all_dynamic_attributes = request.env['product.attribute'].sudo().search([
            ('original_name', '!=', False),
            ('active', '=', True),
            ('company_id', 'in', (False, website.company_id.id))
        ], order='sequence, name')

        product_template_fields = Product._fields
        dynamic_fields_map = {}

        for attr in all_dynamic_attributes:
            field_name = attr.original_name
            if field_name in product_template_fields:
                dynamic_fields_map[attr.name] = {
                    'field_name': field_name,
                    'display_type': attr.display_type,
                    'attribute_id': attr.id,
                    'field_type': product_template_fields[field_name].type,
                }

        # ============================================================
        # NEW ASSOCIATION FLOW
        # ============================================================
        associated_products_by_type = {}

        for assoc in product.product_association_ids.filtered(lambda a: a.association_type_id.active):
            assoc_products = assoc.get_associated_products()
            associated_products_by_type[assoc.association_type_id] = assoc_products

        # Flat list of all products for dynamic value computation
        all_products = product
        for products in associated_products_by_type.values():
            all_products |= products

        # ============================================================
        # READ DYNAMIC VALUES FOR ALL PRODUCTS
        # ============================================================
        product_dynamic_values = {}

        for prod in all_products:
            product_dynamic_values[prod.id] = {}

            for label, info in dynamic_fields_map.items():
                field_name = info['field_name']
                field_type = info['field_type']
                value = getattr(prod, field_name, False)

                if field_type == 'many2one' and value:
                    value = value.name
                elif field_type == 'many2many' and value:
                    value = ', '.join(value.mapped('name'))

                product_dynamic_values[prod.id][label] = value or ''

        dynamic_field_labels = {label: label for label in dynamic_fields_map.keys()}

        # ============================================================
        # SEO SLUG HANDLING
        # ============================================================
        clean_slug = re.sub(r'\s+', '-', product.name.strip()) if product.name else f'product-{product.id}'
        if slug and slug != clean_slug:
            return request.redirect(f"/pxm/shop/{clean_slug}-{product.id}")

        # ============================================================
        # RENDER
        # ============================================================
        return request.render("pim_website.pxm_product_detail", {
            "product": product,
            "image_gallery": image_gallery,

            # Dynamic fields
            "dynamic_price_fields": dynamic_fields_map,
            "product_dynamic_values": product_dynamic_values,
            "dynamic_field_labels": dynamic_field_labels,

            # NEW ASSOCIATION DATA
            "associated_products_by_type": associated_products_by_type,

            # Other
            "clean_slug": clean_slug,
            "attribute_groups": product.get_grouped_dynamic_fields(),
        })

    @http.route('/pxm/shop/compare_data', type='json', auth='public', website=True)
    def get_compare_products_data(self, limit=20, **kw):
        website = request.env['website'].get_current_website()
        company = website.company_id
        website_domain = website.website_domain()

        domain = [('pim_is_published', '=', True)] + website_domain

        products = request.env['product.template'].sudo().search(domain, limit=limit)

        dynamic_fields_map = {}
        all_dynamic_attributes = request.env['product.attribute'].sudo().search([
            ('original_name', '!=', False),
            ('active', '=', True),
            ('company_id', 'in', (False, company.id))
        ])

        product_template_fields = request.env['product.template']._fields
        for attr in all_dynamic_attributes:
            field_name = attr.original_name
            if field_name in product_template_fields:
                dynamic_fields_map[attr.name] = {
                    'field_name': field_name,
                    'display_type': attr.display_type,
                }

        result = []
        for product in products:
            dynamic_values = {}
            for label, info in dynamic_fields_map.items():
                val = getattr(product, info['field_name'])
                if info['display_type'] == 'price':
                    dynamic_values[label] = request.env['ir.qweb.field.monetary'].value_to_html(
                        val, {'display_currency': website.currency_id}) if val else False
                elif hasattr(val, 'name'):
                    dynamic_values[label] = val.name
                elif isinstance(val, list):
                    dynamic_values[label] = ', '.join([str(v) for v in val if v])
                else:
                    dynamic_values[label] = str(val) if val else False

            result.append({
                'id': product.id,
                'name': product.name,
                'price_html': request.env['ir.qweb.field.monetary'].value_to_html(
                    product.list_price, {'display_currency': website.currency_id}),
                'image_1920': product.image_1920,
                'dynamic_values': {k: v for k, v in dynamic_values.items() if v},
            })

        return {'products': result}

