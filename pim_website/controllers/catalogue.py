from odoo import http
from odoo.http import request
from odoo.tools.mail import html2plaintext
import io
import xlsxwriter
from reportlab.pdfgen import canvas

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
import logging
import base64
from PIL import Image
try:
    from PIL.Image import Transpose, Palette, Resampling
except ImportError:
    Transpose = Palette = Resampling = Image

_logger = logging.getLogger(__name__)



class PimProductExport(http.Controller):

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _clean_html(self, value):
        return html2plaintext(value or '').strip()

    def _draw_section_header(self, p, text, y):
        p.setFillColor(HexColor("#EFEFEF"))
        p.rect(40, y - 20, 515, 20, fill=1, stroke=0)

        p.setFillColor(HexColor("#000000"))
        p.setFont("Helvetica-Bold", 11)
        p.drawString(45, y - 14, text)

        return y - 32

    def _draw_kv(self, p, label, value, y,
                 x_label=50, x_value=240,
                 row_height=18):

        # Text
        p.setFont("Helvetica-Bold", 10)
        p.drawString(x_label, y, label)

        p.setFont("Helvetica", 10)
        p.drawString(x_value, y, value)

        # Light gray underline (table row)
        p.setStrokeColor(HexColor("#DADADA"))
        p.setLineWidth(0.5)
        p.line(40, y - 6, 555, y - 6)

        # Padding below row
        return y - row_height

    def _draw_multiline_text(self, p, text, x, y, max_width=480):
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import getSampleStyleSheet

        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.fontSize = 10

        para = Paragraph(text, style)
        w, h = para.wrap(max_width, 100)
        para.drawOn(p, x, y - h)
        return y - h - 10

    def _get_main_product_image_url(self, product):
        """
        Returns absolute URL to product image (PNG/JPEG guaranteed by Odoo)
        """
        images = product.image_ids.filtered(lambda i: i.image_1920)
        if not images:
            return None

        primary = images.filtered(lambda i: i.is_primary)
        image = primary[:1] or images.sorted(key=lambda i: i.sequence)[:1]

        base_url = request.httprequest.host_url.rstrip("/")
        return f"{base_url}/web/image/product.image/{image.id}/image_1920"

    def _prepare_image_for_pdf(self, image_base64, max_w=800):
        """
        Accepts ANY image format (jpg, jpeg, png, webp, cmyk, rgba)
        Returns ImageReader-safe PNG buffer
        """
        try:
            img_bytes = base64.b64decode(image_base64)
            img = Image.open(io.BytesIO(img_bytes))

            # Fix color modes
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode in ("CMYK", "P"):
                img = img.convert("RGB")

            # Resize if too large (memory + spacing control)
            if img.width > max_w:
                ratio = max_w / float(img.width)
                img = img.resize(
                    (int(img.width * ratio), int(img.height * ratio)),
                    Image.Resampling.LANCZOS
                )

            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            buf.seek(0)

            return ImageReader(buf)

        except Exception as e:
            _logger.warning("Image normalization failed: %s", e)
            return None

    def _get_grouped_dynamic_fields(self, product):
        website = request.env['website'].get_current_website()
        company = website.company_id

        product_fields = request.env['product.template']._fields
        rendered_attributes = set()  # avoid duplicates

        groups = request.env['attribute.group'].sudo().search([
            ('active', '=', True),
            ('company_id', '=', company.id),
        ], order='id')

        grouped_data = {}

        for group in groups:

            # ❌ SKIP DEFAULT / FALLBACK GROUP
            if group.name.strip().lower() in ('default', 'general'):
                continue

            lines = group.attribute_group_line_ids.filtered(lambda l: l.enable)

            values = []
            for line in lines:
                attr = line.product_attribute_id
                if not attr or not attr.original_name:
                    continue

                # ❌ Prevent duplicates across groups
                if attr.id in rendered_attributes:
                    continue

                field_name = attr.original_name
                if field_name not in product_fields:
                    continue

                field_type = product_fields[field_name].type
                val = getattr(product, field_name, False)

                if field_type == 'many2one':
                    display_val = val.name if val else ''
                elif field_type == 'many2many':
                    display_val = ', '.join(val.mapped('name')) if val else ''
                else:
                    display_val = self._clean_html(str(val)) if val else ''

                if display_val:
                    values.append((attr.name, display_val))
                    rendered_attributes.add(attr.id)

            if values:
                grouped_data[group.name] = values

        return grouped_data


    @http.route('/pim/product/<int:product_id>/export/pdf', type='http', auth='user')
    def export_pdf(self, product_id, **kw):
        product = request.env['product.template'].sudo().browse(product_id)

        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=A4)
        width, height = A4

        # =================================================
        # HEADER BAND
        # =================================================
        p.setFillColor(HexColor("#714B67"))
        p.rect(0, height - 90, width, 90, fill=1, stroke=0)

        p.setFillColor(HexColor("#FFFFFF"))
        # Product Name (Centered)
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width / 2, height - 45, product.name)

        # SKU + Category (Centered line)
        p.setFont("Helvetica", 10)

        sku_text = f"SKU: {product.default_code or ''}"
        category_text = f"Category: {product.pim_category_ids.name if product.pim_category_ids else ''}"
        family_id = f"Family: {product.family_id.name if product.family_id else ''}"

        p.drawCentredString(
            width / 2,
            height - 65,
            f"{sku_text}    |    {category_text}    |     {family_id}"
        )


        # =================================================
        # DESCRIPTION (RIGHT SIDE)
        # =================================================
        desc_x = 220
        y = height - 150  # aligned with image top

        p.setFont("Helvetica-Bold", 12)
        p.drawString(desc_x, y, "Description")
        y -= 12

        p.setFont("Helvetica", 10)
        y = self._draw_multiline_text(
            p,
            self._clean_html(product.description),
            desc_x,
            y,
            max_width=300
        )

        # Add some spacing before additional images
        y -= 20

        # =================================================
        # MAIN IMAGE + ADDITIONAL IMAGES
        # =================================================

        # Get primary image and additional images from product.image_ids
        primary_image = None
        additional_images = []

        if product.image_ids:
            # Find primary image marked with is_primary=True
            primary_img_record = product.image_ids.filtered(lambda i: i.is_primary and i.image_1920)

            if primary_img_record:
                # Use the primary image
                primary_image = primary_img_record[0].image_1920

                # Get all other images (excluding primary) as additional images
                for img_record in product.image_ids.sorted(key=lambda i: i.sequence):
                    if img_record.image_1920 and img_record.id != primary_img_record[0].id:
                        additional_images.append(img_record.image_1920)
            else:
                # No primary set, take first as primary and rest as additional
                sorted_images = product.image_ids.filtered(lambda i: i.image_1920).sorted(key=lambda i: i.sequence)
                if sorted_images:
                    primary_image = sorted_images[0].image_1920
                    for img_record in sorted_images[1:]:
                        additional_images.append(img_record.image_1920)

        # Fallback: if no images in image_ids, use product.image_1920
        if not primary_image and product.image_1920:
            primary_image = product.image_1920

        # Image positioning
        main_image_x = 40
        main_image_y = height - 150
        main_image_w = 160
        main_image_h = 120

        # Additional images start after description on the right side
        add_image_start_x = desc_x
        add_image_start_y = y  # Start from current y position (after description)
        add_image_w = 80
        add_image_h = 60
        spacing_x = 90  # Horizontal spacing between additional images
        spacing_y = 70  # Vertical spacing for next row

        # Draw PRIMARY IMAGE (large box on left side)
        if primary_image:
            try:
                image_bytes = base64.b64decode(primary_image)
                pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

                png_buffer = io.BytesIO()
                pil_img.save(png_buffer, format="PNG")
                png_buffer.seek(0)

                img = ImageReader(png_buffer)

                p.drawImage(
                    img,
                    main_image_x,
                    main_image_y - main_image_h,
                    width=main_image_w,
                    height=main_image_h,
                    preserveAspectRatio=True,
                    anchor='c'
                )
            except Exception as e:
                _logger.warning("Primary image render failed: %s", e)

        # Draw ADDITIONAL IMAGES (small thumbnails on right side)
        current_add_y = add_image_start_y

        for index, img_base64 in enumerate(additional_images):
            try:
                # Calculate position - 3 images per row
                col = index % 3
                row = index // 3

                x = add_image_start_x + (col * spacing_x)
                current_y = add_image_start_y - (row * spacing_y)

                # Check if we need a new page
                if current_y - add_image_h < 100:
                    p.showPage()
                    add_image_start_y = height - 40
                    current_y = add_image_start_y
                    row = 0
                    col = index % 3
                    x = add_image_start_x + (col * spacing_x)

                image_bytes = base64.b64decode(img_base64)
                pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

                png_buffer = io.BytesIO()
                pil_img.save(png_buffer, format="PNG")
                png_buffer.seek(0)

                img = ImageReader(png_buffer)

                p.drawImage(
                    img,
                    x,
                    current_y - add_image_h,
                    width=add_image_w,
                    height=add_image_h,
                    preserveAspectRatio=True,
                    anchor='c'
                )

                # Update the lowest y position
                current_add_y = min(current_add_y, current_y - add_image_h)

            except Exception as e:
                _logger.warning("Additional image %d render failed: %s", index, e)

        # Calculate y position for attributes section
        # Should start below both main image and additional images
        main_image_bottom = main_image_y - main_image_h
        additional_images_bottom = current_add_y if additional_images else y

        y = min(main_image_bottom, additional_images_bottom) - 20  # Add spacing

        # Ensure we don't go too low on the page
        if y < 100:
            p.showPage()
            y = height - 40

        # =================================================
        # GROUPED ATTRIBUTES
        # =================================================
        grouped_fields = self._get_grouped_dynamic_fields(product)

        for group_name, attributes in grouped_fields.items():

            if y < 100:
                p.showPage()
                y = height - 40

            y = self._draw_section_header(p, group_name, y)

            for label, value in attributes:
                if y < 80:
                    p.showPage()
                    y = height - 40
                    y = self._draw_section_header(p, group_name, y)

                y = self._draw_kv(p, label, value, y)

            y -= 8

        p.save()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename=Product_{product.name}.pdf')
            ]
        )

    # ---------------------------------------------------------
    # Excel Export
    # ---------------------------------------------------------

    @http.route('/pim/product/<int:product_id>/export/excel', type='http', auth='user')
    def export_excel(self, product_id, **kw):

        product = request.env['product.template'].sudo().browse(product_id)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Product Details")

        # -------------------------------------------------
        # FORMATS
        # -------------------------------------------------
        title_fmt = workbook.add_format({
            'bold': True,
            'font_size': 12
        })

        header_fmt = workbook.add_format({
            'bold': True,
            'bg_color': '#E6E6E6',
            'border': 1
        })

        label_fmt = workbook.add_format({
            'bold': True,
            'border': 1,
            'valign': 'top'
        })

        value_fmt = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'valign': 'top'
        })

        # Column width
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 70)

        row = 0

        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------
        sheet.merge_range(row, 0, row, 1, "Product Details", title_fmt)
        row += 2

        # -------------------------------------------------
        # STATIC FIELDS
        # -------------------------------------------------
        static_fields = [
            ("Name", product.name),
            ("SKU", product.default_code or ''),
            # ("Product Type", product.type),
            ("Category", product.categ_id.name if product.categ_id else ''),
            ("Family", product.family_id.name or ''),
            # ("Barcode", product.barcode or ''),
            # ("Sales Price", product.list_price),
            # ("Cost", product.standard_price),
            # ("Company", product.company_id.name if product.company_id else ''),
            ("Description", self._clean_html(product.description)),
        ]

        sheet.write(row, 0, "Basic Product Information", header_fmt)
        sheet.write(row, 1, "", header_fmt)
        row += 1

        for label, value in static_fields:
            sheet.write(row, 0, label, label_fmt)
            sheet.write(row, 1, value, value_fmt)
            row += 1

        row += 2

        # -------------------------------------------------
        # DYNAMIC ATTRIBUTE GROUPS
        # -------------------------------------------------
        grouped_fields = self._get_grouped_dynamic_fields(product)

        for group_name, attributes in grouped_fields.items():

            # Group header
            sheet.write(row, 0, group_name, header_fmt)
            sheet.write(row, 1, "", header_fmt)
            row += 1

            for label, value in attributes:
                sheet.write(row, 0, label, label_fmt)
                sheet.write(row, 1, value, value_fmt)
                row += 1

            row += 2  # spacing between groups

        # -------------------------------------------------
        # FINALIZE
        # -------------------------------------------------
        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                (
                    'Content-Type',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ),
                (
                    'Content-Disposition',
                    f'attachment; filename=Product_{product.name}.xlsx'
                )
            ]
        )
