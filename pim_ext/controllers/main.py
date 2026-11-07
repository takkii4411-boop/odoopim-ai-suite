from odoo import http
from odoo.addons.html_editor.controllers.main import HTML_Editor
from odoo.http import request
import base64
import time
import io
from werkzeug.utils import secure_filename
from odoo.addons.html_editor.tools import get_video_url_data
from odoo.http import Response
import json


class VideoStreamController(http.Controller):

    @http.route('/pim_ext/video/<int:image_id>', type='http', auth='user', csrf=False)
    def stream_video(self, image_id, **kwargs):
        """Stream video file with partial content support for seeking"""
        try:
            image = request.env['product.image'].sudo().browse(image_id)

            if not image.exists() or not image.video_file:
                return request.make_response("Video not found", 404)

            try:
                video_data = base64.b64decode(image.video_file)
            except Exception as e:
                _logger.error(f"Failed to decode video data: {e}")
                return request.make_response("Invalid video data", 500)

            video_size = len(video_data)

            # Determine content type
            content_type = 'video/mp4'
            if image.video_filename:
                ext = image.video_filename.split('.')[-1].lower()
                content_type_map = {
                    'webm': 'video/webm',
                    'ogg': 'video/ogg',
                    'mov': 'video/quicktime',
                    'mp4': 'video/mp4'
                }
                content_type = content_type_map.get(ext, 'video/mp4')

            # Handle Range requests for video seeking
            range_header = request.httprequest.headers.get('Range')

            if range_header:
                byte_range = range_header.replace('bytes=', '').split('-')
                start = int(byte_range[0]) if byte_range[0] else 0
                end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else video_size - 1
                end = min(end, video_size - 1)
                length = end - start + 1

                response = request.make_response(
                    video_data[start:end+1],
                    headers={
                        'Content-Type': content_type,
                        'Content-Range': f'bytes {start}-{end}/{video_size}',
                        'Accept-Ranges': 'bytes',
                        'Content-Length': str(length),
                        'Cache-Control': 'public, max-age=3600',
                    }
                )
                response.status_code = 206
                return response

            return request.make_response(
                video_data,
                headers={
                    'Content-Type': content_type,
                    'Content-Length': str(video_size),
                    'Accept-Ranges': 'bytes',
                    'Cache-Control': 'public, max-age=3600',
                }
            )

        except Exception as e:
            _logger.error(f"Error streaming video {image_id}: {str(e)}", exc_info=True)
            return request.make_response("Error streaming video", 500)

    @http.route('/pim_ext/video/thumbnail/<int:image_id>', type='http', auth='user')
    def video_thumbnail(self, image_id, **kwargs):
        """Return placeholder thumbnail for video files"""
        svg_placeholder = '''
        <svg width="200" height="150" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="150" fill="#333"/>
            <circle cx="100" cy="75" r="30" fill="#fff" opacity="0.8"/>
            <polygon points="92,60 92,90 115,75" fill="#333"/>
        </svg>
        '''
        return Response(svg_placeholder, headers={'Content-Type': 'image/svg+xml'})


# =============================================================================
# CUSTOM HTML EDITOR CONTROLLER
# =============================================================================

class CustomHTML_Editor(HTML_Editor):

    @http.route(['/web_editor/video_url/data', '/html_editor/video_url/data'],
                type='json', auth='user', website=True)
    def video_url_data(self, video_url, autoplay=False, loop=False,
                       hide_controls=False, hide_fullscreen=False,
                       hide_dm_logo=False, hide_dm_share=False):
        """Handle both uploaded and external videos"""

        if video_url.startswith('/web/content/'):
            # Extract attachment ID from URL (e.g., /web/content/123?...)
            try:
                attachment_id = int(video_url.split('/web/content/')[1].split('?')[0])
                attachment = request.env['ir.attachment'].browse(attachment_id).exists()

                if not attachment:
                    return {'error': 'Attachment not found'}

                # Return data for uploaded video
                return {
                    'embed_url': video_url,
                    'video_id': str(attachment_id),
                    'params': '',
                    'platform': 'uploaded',
                }
            except (ValueError, IndexError):
                return {'error': 'Invalid uploaded video URL'}

        # Delegate to existing logic for external video platforms
        return get_video_url_data(
            video_url, autoplay=autoplay, loop=loop,
            hide_controls=hide_controls, hide_fullscreen=hide_fullscreen,
            hide_dm_logo=hide_dm_logo, hide_dm_share=hide_dm_share
        )

    @http.route('/web_editor/video_upload', type='http', auth='user',
                website=True, methods=['POST'], csrf=False)
    def video_upload(self, **kwargs):
        """Handle video upload in HTML editor"""

        if 'file' not in request.httprequest.files:
            print("No file uploaded")  # Debugging print statement
            return request.make_json_response({'error': 'No file uploaded'}, status=400)

        file = request.httprequest.files['file']
        if not file:
            print("No file uploaded")  # Debugging print statement
            return request.make_json_response({'error': 'No file uploaded'}, status=400)

        # Sanitize the filename
        safe_filename = secure_filename(file.filename)
        print(f"Sanitized filename: {safe_filename}")  # Debugging print statement

        # Read the file content and encode it in base64
        file_content = file.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        print("File read and encoded in base64")  # Debugging print statement

        # Determine MIME type
        mimetype = 'video/mp4'
        if safe_filename.lower().endswith('.webm'):
            mimetype = 'video/webm'
        elif safe_filename.lower().endswith('.ogg'):
            mimetype = 'video/ogg'
        print(f"Detected MIME type: {mimetype}")  # Debugging print statement

        try:
            # Create an ir.attachment record
            attachment = request.env['ir.attachment'].create({
                'name': safe_filename,
                'datas': file_base64,
                'res_model': 'html_editor.video',
                'res_id': 0,
                'type': 'binary',
                'mimetype': mimetype,
                'public': True,
            })
            print(f"Attachment created with ID: {attachment.id}")  # Debugging print statement

            # Generate the URL for the uploaded video
            video_url = f'/web/content/{attachment.id}?download=true&t={int(time.time())}'
            print(f"Generated video URL: {video_url}")  # Debugging print statement

            return request.make_json_response({'url': video_url, 'video_id': attachment.id})

        except Exception as e:
            _logger.error(f"Error creating attachment: {e}")
            return request.make_json_response({'error': str(e)}, status=500)
