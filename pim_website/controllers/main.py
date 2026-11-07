from odoo import http
from odoo.http import request
from odoo import fields
import json

try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None


class PXMShopController(http.Controller):

    @http.route([
        '/pxm/shop',
        '/pxm/shop/page/<int:page>',
    ], type='http', auth='public', website=True, csrf=False)
    def pxm_shop(self, page=1, **kw):
        """
        Main shop page - renders initial page structure
        """
        if not request.website.has_ecommerce_access():
            return request.redirect(f'/web/login?redirect={request.httprequest.path}')

        website = request.env['website'].get_current_website()
        company = website.company_id

        # Load filter options
        company_domain = [
            '|',
            ('company_id', '=', False),
            ('company_id', '=', company.id)
        ]

        families = request.env['family.attribute'].sudo().search(
            company_domain, order='name'
        )
        categories = request.env['pim.category'].sudo().search(
            company_domain, order='name'
        )
        brands = request.env['product.brand'].sudo().search(
            company_domain, order='name'
        )

        values = {
            'families': families,
            'categories': categories,
            'brands': brands,
            'website': website,
            'currency_symbol': website.currency_id.symbol,
        }

        return request.render("pim_website.pxm_shop_template", values)

    @http.route('/pxm/shop/filter_data', type='json', auth='public', website=True, csrf=False)
    def shop_filter_data(self, **kw):
        """
        AJAX endpoint for dynamic product filtering
        Returns JSON with products and metadata
        """
        try:
            # Extract filter parameters
            search = kw.get('search', '').strip()
            family_ids = kw.get('family_ids', [])
            category_ids = kw.get('category_ids', [])
            brand_ids = kw.get('brand_ids', [])
            page = int(kw.get('page', 1))
            limit = int(kw.get('limit', 20))

            # Website and company context
            website = request.env['website'].get_current_website()
            company = website.company_id
            website_domain = website.website_domain()

            # Build domain
            domain = [('pim_is_published', '=', True)] + website_domain

            # Apply search filter
            if search:
                domain += [
                    '|', '|',
                    ('name', 'ilike', search),
                    ('default_code', 'ilike', search),
                    ('description_sale', 'ilike', search),
                ]

            # Apply multi-select filters
            if family_ids and isinstance(family_ids, list):
                family_int_ids = [int(x) for x in family_ids if str(x).isdigit()]
                if family_int_ids:
                    domain.append(('family_id', 'in', family_int_ids))

            if category_ids and isinstance(category_ids, list):
                category_int_ids = [int(x) for x in category_ids if str(x).isdigit()]
                if category_int_ids:
                    domain.append(('pim_category_ids', 'in', category_int_ids))

            if brand_ids and isinstance(brand_ids, list):
                brand_int_ids = [int(x) for x in brand_ids if str(x).isdigit()]
                if brand_int_ids:
                    domain.append(('brand_id', 'in', brand_int_ids))

            # Fetch products
            ProductSudo = request.env['product.template'].sudo()
            total_products = ProductSudo.search_count(domain)

            offset = (page - 1) * limit
            products = ProductSudo.search(
                domain,
                offset=offset,
                limit=limit,
                order="sequence asc, name asc"
            )

            # Get currency conversion rate
            company_currency = company.sudo().currency_id
            conversion_rate = request.env['res.currency']._get_conversion_rate(
                company_currency,
                website.currency_id,
                company,
                fields.Date.today()
            )

            # Load dynamic attributes
            all_dynamic_attributes = request.env['product.attribute'].sudo().search([
                ('original_name', '!=', False),
                ('active', '=', True),
                ('company_id', 'in', (False, company.id))
            ], order='sequence, name')

            product_template_fields = request.env['product.template']._fields
            dynamic_fields_map = {}

            for attr in all_dynamic_attributes:
                field_name = attr.original_name
                if field_name in product_template_fields:
                    dynamic_fields_map[attr.name] = {
                        'field_name': field_name,
                        'display_type': attr.display_type,
                        'field_type': product_template_fields[field_name].type,
                    }

            # Build product list
            product_list = []
            for product in products:
                # Get dynamic values
                dynamic_values = {}
                for label, info in dynamic_fields_map.items():
                    val = getattr(product, info['field_name'], False)
                    if info['field_type'] == 'many2one':
                        dynamic_values[label] = val.name if val else None
                    elif info['field_type'] == 'many2many':
                        dynamic_values[label] = ', '.join(val.mapped('name')) if val else None
                    else:
                        dynamic_values[label] = val

                # Format price
                price_value = product.list_price * conversion_rate
                price_html = f"{website.currency_id.symbol}{price_value:,.2f}"

                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'default_code': product.default_code or '',
                    'description_sale': product.description or 'No description available.',
                    'price': price_value,
                    'price_html': price_html,
                    'image_1920': product.image_1920.decode('utf-8') if product.image_1920 else '',
                    'variant_count': len(product.product_variant_ids),
                    'url': f'/pxm/shop/product-{product.id}',
                    'dynamic_values': dynamic_values,
                }

                product_list.append(product_data)

            # Calculate pagination
            total_pages = (total_products + limit - 1) // limit

            return {
                'success': True,
                'products': product_list,
                'currency_symbol': website.currency_id.symbol,
                'total_products': total_products,
                'current_page': page,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages,
            }


        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'products': [],
                'total_products': 0,
            }