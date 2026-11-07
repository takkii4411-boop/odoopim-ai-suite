/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, useRef, onWillUpdateProps } from "@odoo/owl";
import { getDataURLFromFile } from "@web/core/utils/urls";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class EnhancedMediaGalleryDialog extends Component {
    static template = "pim_ext.EnhancedMediaGalleryDialog";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.notification = useService("notification");
        this.orm = useService("orm");
        
        this.fileInputGallery = useRef("file_input_gallery");
        this.fileUploadInput = useRef("file_upload_input");
        
        this.state = useState({
            showDialog: false,
            showUploadOptionsDialog: false,
            uploadMethod: null,
            isRemovingBackground: false,
            isRestoringBackground: false,
            currentIndex: 0,
            isDragging: false,
            isPlaying: false,
            videoProgress: 0,
            showDragZoneOnly: false,
            
            // URL Upload
            currentUrl: "",
            urlList: [],
            selectedUrlIndex: 0,
            isUploadingUrls: false,
            
            // File Upload
            filesToUpload: [],
            selectedFileIndex: 0,
            isUploadingFiles: false,
            uploadProgress: 0,
            updateTrigger: 0,
        });

        onWillUpdateProps((nextProps) => {
            const nextRecords = nextProps.record.data[nextProps.name]?.records || [];
            if (this.state.currentIndex >= nextRecords.length && nextRecords.length > 0) {
                this.state.currentIndex = nextRecords.length - 1;
            }
        });
    }

    // =================================================================
    // GETTERS
    // =================================================================

    get currentBgRemoved() {
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly && 
            this.state.currentIndex < this.state.filesToUpload.length) {
            const file = this.state.filesToUpload[this.state.currentIndex];
            return file?.bgRemoved === true;
        }
        
        const record = this.currentItem;
        if (!record) return false;
        
        return record.data.bg_removed === true || record.data.bg_removed === 1;
    }

    get currentHasOriginal() {
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly && 
            this.state.currentIndex < this.state.filesToUpload.length) {
            const file = this.state.filesToUpload[this.state.currentIndex];
            return !!file?.originalPreview;
        }
        
        const record = this.currentItem;
        return !!record?.data.image_1920_original;
    }

    get mediaItems() {
        const field = this.props.record.data[this.props.name];
        return field ? field.records : [];
    }

    get currentItem() {
        return this.mediaItems[this.state.currentIndex];
    }

    get selectedUrlItem() {
        return this.state.urlList[this.state.selectedUrlIndex];
    }

    get selectedFileItem() {
        return this.state.filesToUpload[this.state.selectedFileIndex];
    }
    
    get shouldShowDragZone() {
        // Show drag zone when:
        // 1. Explicitly set to show drag zone only (fresh drag & drop mode)
        // 2. No files in preview AND no saved media
        return this.state.showDragZoneOnly || 
               (this.state.filesToUpload.length === 0 && this.mediaItems.length === 0);
    }

    get shouldShowMediaSlider() {
        return !this.state.showDragZoneOnly && 
               (this.state.filesToUpload.length > 0 || this.mediaItems.length > 0);
    }

    getCurrentMediaUrl() {
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly) {
            const file = this.state.filesToUpload[this.state.currentIndex];
            return file ? file.preview : "";
        }

        const record = this.currentItem;
        if (!record) return "";

        if (record.data.video_url) {
            return record.data.video_url;
        }

        if (record.data.video_file) {
            if (record.resId && typeof record.resId === 'number') {
                return `/pim_ext/video/${record.resId}`;
            }
            if (record.data.video_file.startsWith('data:')) {
                return record.data.video_file;
            }
            return `data:video/mp4;base64,${record.data.video_file}`;
        }

        if (record.data.image_1920) {
            const imageData = record.data.image_1920;
            
            if (imageData.startsWith('data:')) {
                return imageData;
            }
            
            if (record.resId && typeof record.resId === 'number') {
                return `/web/image/${record.resModel}/${record.resId}/image_1920?t=${this.state.updateTrigger}`;
            }
            
            return `data:image/png;base64,${imageData}`;
        }

        if (record.resId && typeof record.resId === 'number') {
            return `/web/image/${record.resModel}/${record.resId}/image_1920`;
        }

        return "";
    }

    isEmbedVideo() {
        const url = this.getCurrentMediaUrl();
        if (!url) return false;
        return url.includes('youtube.com') || url.includes('youtu.be') || url.includes('vimeo.com');
    }

    getEmbedUrl() {
        let url = this.getCurrentMediaUrl();
        if (!url) return "";

        if (url.includes('youtube.com') || url.includes('youtu.be')) {
            let videoId = null;
            
            if (url.includes('watch?v=')) {
                const urlParams = new URLSearchParams(url.split('?')[1]);
                videoId = urlParams.get('v');
            } else if (url.includes('youtu.be/')) {
                videoId = url.split('youtu.be/')[1].split('?')[0].split('/')[0];
            } else if (url.includes('/embed/')) {
                videoId = url.split('/embed/')[1].split('?')[0];
            } else if (url.includes('/shorts/')) {
                videoId = url.split('/shorts/')[1].split('?')[0];
            }
            
            if (videoId) {
                return `https://www.youtube.com/embed/${videoId}?autoplay=0`;
            }
        }
        
        if (url.includes('vimeo.com')) {
            const regExp = /^.*(vimeo\.com\/)((channels\/[A-z]+\/)|(groups\/[A-z]+\/videos\/))?([0-9]+)/;
            const match = url.match(regExp);
            if (match && match[5]) {
                return `https://player.vimeo.com/video/${match[5]}`;
            }
        }

        return url;
    }

    getVideoMimeType() {
        // PREVIEW MODE
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly) {
            const file = this.state.filesToUpload[this.state.currentIndex];
            if (!file) return 'video/mp4';
            
            const filename = file.name || '';
            if (filename.toLowerCase().endsWith('.webm')) return 'video/webm';
            if (filename.toLowerCase().endsWith('.ogg')) return 'video/ogg';
            if (filename.toLowerCase().endsWith('.mov')) return 'video/quicktime';
            return 'video/mp4';
        }

        // NORMAL MODE
        const record = this.currentItem;
        if (!record) return 'video/mp4';
        
        const filename = record.data.video_filename || record.data.name || '';
        
        if (filename.toLowerCase().endsWith('.webm')) return 'video/webm';
        if (filename.toLowerCase().endsWith('.ogg')) return 'video/ogg';
        if (filename.toLowerCase().endsWith('.mov')) return 'video/quicktime';
        
        return 'video/mp4';
    }

    isVideo() {
        // PREVIEW MODE
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly) {
            const file = this.state.filesToUpload[this.state.currentIndex];
            return file ? file.type === 'video' : false;
        }

        // NORMAL MODE
        const record = this.currentItem;
        return record && (record.data.video_file || record.data.video_url);
    }

    isPrimary() {
        // PREVIEW MODE
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly) {
            const file = this.state.filesToUpload[this.state.currentIndex];
            return file ? file.setPrimary === true : false;
        }

        // NORMAL MODE
        const record = this.currentItem;
        return record && record.data.is_primary;
    }

    hasBgRemoved() {
        return this.currentBgRemoved;
    }

    // =================================================================
    // DIALOG CONTROL
    // =================================================================

    openDialog() {
        this.state.showDialog = true;
    }

    closeDialog() {
        this.state.showDialog = false;
        this.state.showDragZoneOnly = false;
        // Clear preview when closing
        this.state.filesToUpload = [];
    }

    openUploadOptionsDialog() {
        this.state.showUploadOptionsDialog = true;
        this.state.uploadMethod = null;
        this.state.currentUrl = "";
        this.state.urlList = [];
        this.state.selectedUrlIndex = 0;
        this.state.filesToUpload = [];
        this.state.selectedFileIndex = 0;
    }

    closeUploadOptionsDialog() {
        this.state.showUploadOptionsDialog = false;
        this.state.uploadMethod = null;
        this.state.currentUrl = "";
        this.state.urlList = [];
        this.state.filesToUpload = [];
    }

    selectUploadMethod(method) {
        this.state.uploadMethod = method;
        
        if (method === 'drag') {
            this.closeUploadOptionsDialog();
            this.state.filesToUpload = [];
            this.state.currentIndex = 0;
            this.state.showDragZoneOnly = true;
            this.openDialog();
        }
    }

    // =================================================================
    // PRIMARY LOGIC
    // =================================================================

    togglePrimaryForFile(index) {
        const clickedFile = this.state.filesToUpload[index];
        
        if (clickedFile.type !== 'image') {
            this.notification.add(_t("Only images can be set as primary"), { type: "warning" });
            return;
        }
        
        const isCurrentlyPrimary = clickedFile.setPrimary;
        
        this.state.filesToUpload.forEach((file, i) => {
            file.setPrimary = (i === index) ? !isCurrentlyPrimary : false;
        });
        
        const message = isCurrentlyPrimary 
            ? _t("Primary unmarked") 
            : _t("Primary marked (will save when you click 'Save')");
        this.notification.add(message, { type: "info" });
    }

    togglePrimaryForUrl(index) {
        const clickedUrl = this.state.urlList[index];
        
        if (!clickedUrl.isImage) {
            this.notification.add(_t("Only images can be set as primary"), { type: "warning" });
            return;
        }
        
        const isCurrentlyPrimary = clickedUrl.setPrimary;
        
        this.state.urlList.forEach((url, i) => {
            url.setPrimary = (i === index) ? !isCurrentlyPrimary : false;
        });
        
        const message = isCurrentlyPrimary 
            ? _t("Primary unmarked") 
            : _t("Primary marked (will save when you click 'Upload')");
        this.notification.add(message, { type: "info" });
    }

    async setPrimary() {
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly) {
            this.togglePrimaryForFile(this.state.currentIndex);
            return;
        }

        const currentRecord = this.currentItem;
        if (!currentRecord || this.isVideo()) {
            this.notification.add(_t("Only images can be set as primary"), { type: "warning" });
            return;
        }

        try {
            const isCurrentlyPrimary = currentRecord.data.is_primary;
            const newPrimaryStatus = !isCurrentlyPrimary;
            
            if (!currentRecord.resId) {
                this.mediaItems.forEach(item => {
                    item.data.is_primary = false;
                });
                currentRecord.data.is_primary = newPrimaryStatus;
                
                this.notification.add(
                    newPrimaryStatus ? _t("Primary set (unsaved)") : _t("Primary unset (unsaved)"), 
                    { type: "info" }
                );
                return;
            }

            const commands = [];
            for (const record of this.mediaItems) {
                if (record.resId) {
                    const shouldBePrimary = (record.resId === currentRecord.resId) ? newPrimaryStatus : false;
                    commands.push([1, record.resId, { is_primary: shouldBePrimary }]);
                }
            }

            if (commands.length > 0) {
                await this.props.record.update({
                    [this.props.name]: commands
                });
            }

            this.notification.add(
                newPrimaryStatus ? _t("Primary image updated") : _t("Primary image removed"), 
                { type: "success" }
            );

        } catch (error) {
            this.notification.add(_t("Error updating primary"), { type: "danger" });
        }
    }

    // =================================================================
    // URL UPLOAD METHODS
    // =================================================================

    onUrlInputKeydown(ev) {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            this.addUrlToList();
        }
    }

    onUrlInputPaste(ev) {
        setTimeout(() => {
            const pastedText = this.state.currentUrl || "";
            const urls = pastedText.split(/[\n\r]+/).map(u => u.trim()).filter(u => u);
            
            if (urls.length > 1) {
                ev.preventDefault();
                this.state.currentUrl = "";
                urls.forEach(url => {
                    this.addSingleUrl(url);
                });
            }
        }, 10);
    }

    async addUrlToList() {
        const url = (this.state.currentUrl || "").trim();
        await this.addSingleUrl(url);
        this.state.currentUrl = "";
    }

    async addSingleUrl(url) {
        if (!url) {
            this.notification.add(_t("Please enter a URL"), { type: "warning" });
            return;
        }

        if (!this.isValidUrl(url)) {
            this.notification.add(_t("Invalid URL format"), { type: "warning" });
            return;
        }

        const exists = this.state.urlList.some(item => item.url === url);
        if (exists) {
            this.notification.add(_t("URL already added"), { type: "warning" });
            return;
        }

        const urlItem = {
            url: url,
            preview: null,
            isImage: false,
            isVideo: false,
            loading: true,
            error: null,
            size: null,
            format: null,
            setPrimary: false,
            bgRemoved: false,
            originalPreview: null,
        };

        this.state.urlList.push(urlItem);
        this.state.selectedUrlIndex = this.state.urlList.length - 1;

        if (url.startsWith('data:image/')) {
            await this.handleDataUrl(urlItem);
        } else {
            await this.fetchUrlPreview(urlItem);
        }
    }

    async handleDataUrl(urlItem) {
        try {
            const matches = urlItem.url.match(/^data:([^;]+);base64,(.+)$/);
            
            if (!matches) {
                urlItem.loading = false;
                urlItem.error = "Invalid data URL format";
                return;
            }

            const mimeType = matches[1];
            const base64Data = matches[2];

            if (mimeType.startsWith('image/')) {
                urlItem.loading = false;
                urlItem.isImage = true;
                urlItem.isVideo = false;
                urlItem.preview = urlItem.url;
                urlItem.format = mimeType.split('/')[1].toUpperCase();
                
                const sizeInBytes = (base64Data.length * 3) / 4;
                urlItem.size = (sizeInBytes / (1024 * 1024)).toFixed(2);
            } else {
                urlItem.loading = false;
                urlItem.error = "Unsupported data URL type";
            }
        } catch (error) {
            urlItem.loading = false;
            urlItem.error = error.message || "Failed to process data URL";
        }
    }

    isYoutubeUrl(url) {
        return url.includes('youtube.com') || url.includes('youtu.be');
    }

    isVimeoUrl(url) {
        return url.includes('vimeo.com');
    }

    getYoutubeEmbedUrl(url) {
        let videoId = null;
        
        if (url.includes('watch?v=')) {
            const urlParams = new URLSearchParams(url.split('?')[1]);
            videoId = urlParams.get('v');
        } else if (url.includes('youtu.be/')) {
            videoId = url.split('youtu.be/')[1].split('?')[0].split('/')[0];
        } else if (url.includes('/embed/')) {
            videoId = url.split('/embed/')[1].split('?')[0];
        } else if (url.includes('/shorts/')) {
            videoId = url.split('/shorts/')[1].split('?')[0];
        }
        
        if (videoId) {
            return `https://www.youtube.com/embed/${videoId}?autoplay=0`;
        }
        
        return url;
    }

    getVimeoEmbedUrl(url) {
        const regExp = /^.*(vimeo\.com\/)((channels\/[A-z]+\/)|(groups\/[A-z]+\/videos\/))?([0-9]+)/;
        const match = url.match(regExp);
        if (match && match[5]) {
            return `https://player.vimeo.com/video/${match[5]}`;
        }
        return url;
    }

    removeUrlFromList(index) {
        this.state.urlList.splice(index, 1);
        
        if (this.state.selectedUrlIndex >= this.state.urlList.length) {
            this.state.selectedUrlIndex = Math.max(0, this.state.urlList.length - 1);
        }
    }

    selectUrlPreview(index) {
        this.state.selectedUrlIndex = index;
    }

    prevUrlPreview() {
        if (this.state.urlList.length === 0) return;
        
        if (this.state.selectedUrlIndex > 0) {
            this.state.selectedUrlIndex--;
        } else {
            this.state.selectedUrlIndex = this.state.urlList.length - 1;
        }
    }

    nextUrlPreview() {
        if (this.state.urlList.length === 0) return;
        
        if (this.state.selectedUrlIndex < this.state.urlList.length - 1) {
            this.state.selectedUrlIndex++;
        } else {
            this.state.selectedUrlIndex = 0;
        }
    }

    async fetchUrlPreview(urlItem) {
        urlItem.bgRemoved = false;
        urlItem.originalPreview = null;
        
        try {
            if (this.isYoutubeUrl(urlItem.url)) {
                urlItem.loading = false;
                urlItem.isVideo = true;
                urlItem.isImage = false;
                urlItem.preview = this.getYoutubeEmbedUrl(urlItem.url);
                urlItem.format = "YOUTUBE";
                urlItem.size = "N/A";
                return;
            }
            
            if (this.isVimeoUrl(urlItem.url)) {
                urlItem.loading = false;
                urlItem.isVideo = true;
                urlItem.isImage = false;
                urlItem.preview = this.getVimeoEmbedUrl(urlItem.url);
                urlItem.format = "VIMEO";
                urlItem.size = "N/A";
                return;
            }

            const result = await this.orm.call(
                "product.image",
                "fetch_url_content",
                [urlItem.url]
            );

            if (result.success) {
                urlItem.loading = false;
                urlItem.isImage = result.isImage;
                urlItem.isVideo = result.isVideo;
                urlItem.size = result.size ? (result.size / (1024 * 1024)).toFixed(2) : "N/A";
                urlItem.format = result.contentType ? result.contentType.split('/')[1].toUpperCase() : "UNKNOWN";
                
                if (result.isImage && result.data) {
                    urlItem.preview = `data:${result.contentType};base64,${result.data}`;
                } else if (result.isVideo && result.data) {
                    urlItem.preview = `data:${result.contentType};base64,${result.data}`;
                } else if (result.isVideo) {
                    urlItem.preview = urlItem.url;
                }
            } else {
                urlItem.loading = false;
                urlItem.error = result.error || "Failed to load";
            }
        } catch (error) {
            urlItem.loading = false;
            urlItem.error = error.message || "Failed to load";
        }
    }

    async uploadFromUrls() {
        if (this.state.urlList.length === 0) {
            this.notification.add(_t("No URLs added"), { type: "warning" });
            return;
        }

        this.state.isUploadingUrls = true;

        try {
            const commands = [];

            for (let i = 0; i < this.state.urlList.length; i++) {
                const urlItem = this.state.urlList[i];
                
                const fileName = this.extractFilenameFromUrl(urlItem.url) || `url_media_${Date.now()}_${i}`;
                
                const values = {
                    name: fileName,
                    upload_method: "url",
                    is_primary: urlItem.setPrimary || false,
                    sequence: i + 1,
                };

                if (urlItem.isVideo) {
                    values.video_url = urlItem.url;
                }

                if (urlItem.isImage) {
                    let imageData;
                    
                    if (urlItem.url.startsWith('data:image/')) {
                        imageData = urlItem.preview.split(',')[1];
                    } else {
                        const result = await this.orm.call(
                            "product.image",
                            "fetch_url_content",
                            [urlItem.url]
                        );

                        if (!result.success || !result.data) {
                            this.notification.add(_t(`Failed to fetch: ${urlItem.url}`), { type: "warning" });
                            continue;
                        }
                        
                        imageData = result.data;
                    }

                    if (urlItem.bgRemoved && urlItem.preview) {
                        imageData = urlItem.preview.split(',')[1];
                    }

                    values.image_1920 = imageData;
                    
                    if (urlItem.bgRemoved && urlItem.originalPreview) {
                        values.bg_removed = true;
                        values.image_1920_original = urlItem.originalPreview.split(',')[1];
                    } else {
                        values.bg_removed = false;
                    }
                }

                commands.push([0, 0, values]);
            }

            if (commands.length > 0) {
                await this.props.record.update({
                    [this.props.name]: commands
                });

                this.notification.add(_t(`${commands.length} URL(s) added successfully`), { type: "success" });
                this.closeUploadOptionsDialog();
            } else {
                this.notification.add(_t("No valid URLs to upload"), { type: "warning" });
            }

        } catch (e) {
            this.notification.add(_t("Some URLs failed to upload"), { type: "warning" });
        } finally {
            this.state.isUploadingUrls = false;
        }
    }

    async removeBackgroundFromUrl(index) {
        const urlItem = this.state.urlList[index];
        
        if (!urlItem || !urlItem.isImage) {
            this.notification.add(_t("Only images can have background removed"), { type: "warning" });
            return;
        }

        if (!urlItem.preview) {
            this.notification.add(_t("Please wait for preview to load"), { type: "warning" });
            return;
        }

        this.state.isRemovingBackground = true;

        try {
            let imageData = urlItem.preview;
            if (imageData.startsWith('data:')) {
                imageData = imageData.split(',')[1];
            }

            if (!urlItem.originalPreview) {
                urlItem.originalPreview = urlItem.preview;
                urlItem.bgRemoved = false;
            }

            const result = await this.orm.call(
                "product.image",
                "remove_background",
                [imageData]
            );

            if (result.success && result.data) {
                urlItem.preview = `data:image/png;base64,${result.data}`;
                urlItem.bgRemoved = true;
                urlItem.format = 'PNG';
                
                this.notification.add(_t("Background removed. Will be saved when you upload."), { type: "success" });
            } else {
                this.notification.add(_t("Failed: " + (result.error || "Unknown error")), { type: "danger" });
            }
        } catch (error) {
            this.notification.add(_t("Error: " + error.message), { type: "danger" });
        } finally {
            this.state.isRemovingBackground = false;
        }
    }

    async restoreBackgroundFromUrl(index) {
        const urlItem = this.state.urlList[index];
        
        if (!urlItem || !urlItem.originalPreview) {
            this.notification.add(_t("No original to restore"), { type: "warning" });
            return;
        }

        urlItem.preview = urlItem.originalPreview;
        urlItem.bgRemoved = false;
        this.notification.add(_t("Original restored"), { type: "success" });
    }

    // =================================================================
    // FILE UPLOAD METHODS
    // =================================================================

    onFileUploadClick() {
        if (this.fileUploadInput.el) {
            this.fileUploadInput.el.click();
        }
    }

    async onFileSelectForPreview(ev) {
        const files = Array.from(ev.target.files);

        for (const file of files) {
            const isImage = file.type.startsWith("image/");
            const isVideo = file.type.startsWith("video/");

            if (!isImage && !isVideo) {
                this.notification.add(_t(`${file.name} is not a valid image or video`), { type: "warning" });
                continue;
            }

            if (file.size > 10 * 1024 * 1024) {
                this.notification.add(_t(`${file.name} exceeds 10MB limit`), { type: "warning" });
                continue;
            }

            const fileObj = {
                file: file,
                name: file.name,
                size: (file.size / (1024 * 1024)).toFixed(2),
                type: isVideo ? 'video' : 'image',
                format: file.name.split('.').pop().toUpperCase(),
                preview: null,
                setPrimary: false,
                bgRemoved: false,
                originalPreview: null,
            };

            try {
                const dataUrl = await getDataURLFromFile(file);
                fileObj.preview = dataUrl;
            } catch (error) {
                // Silent fail - preview not critical
            }

            this.state.filesToUpload.push(fileObj);
        }

        if (this.state.filesToUpload.length > 0) {
            this.state.selectedFileIndex = this.state.filesToUpload.length - files.length;
            this.state.showDragZoneOnly = false;
        }

        ev.target.value = "";
    }

    removeFileFromPreview(index) {
        this.state.filesToUpload.splice(index, 1);
        
        if (this.state.selectedFileIndex >= this.state.filesToUpload.length) {
            this.state.selectedFileIndex = Math.max(0, this.state.filesToUpload.length - 1);
        }
        
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly) {
            if (this.state.currentIndex >= this.state.filesToUpload.length) {
                this.state.currentIndex = Math.max(0, this.state.filesToUpload.length - 1);
            }
        }

        if (this.state.filesToUpload.length === 0) {
            this.state.showDragZoneOnly = true;
        }
    }

    selectFilePreview(index) {
        this.state.selectedFileIndex = index;
    }

    prevFilePreview() {
        if (this.state.filesToUpload.length === 0) return;
        
        if (this.state.selectedFileIndex > 0) {
            this.state.selectedFileIndex--;
        } else {
            this.state.selectedFileIndex = this.state.filesToUpload.length - 1;
        }
    }

    nextFilePreview() {
        if (this.state.filesToUpload.length === 0) return;
        
        if (this.state.selectedFileIndex < this.state.filesToUpload.length - 1) {
            this.state.selectedFileIndex++;
        } else {
            this.state.selectedFileIndex = 0;
        }
    }

    async uploadSelectedFiles() {
        if (this.state.filesToUpload.length === 0) {
            this.notification.add(_t("No files selected"), { type: "warning" });
            return;
        }

        this.state.isUploadingFiles = true;

        try {
            const commands = [];

            for (let i = 0; i < this.state.filesToUpload.length; i++) {
                const fileItem = this.state.filesToUpload[i];
                const base64Data = fileItem.preview.split(",")[1];
                const fileName = fileItem.name || `media_${Date.now()}_${i}`;
                
                const values = {
                    name: fileName,
                    upload_method: "upload",
                    is_primary: fileItem.setPrimary || false,
                    sequence: i + 1,
                };

                if (fileItem.type === "image") {
                    values.image_1920 = base64Data;
                    
                    if (fileItem.bgRemoved && fileItem.originalPreview) {
                        values.bg_removed = true;
                        values.image_1920_original = fileItem.originalPreview.split(',')[1];
                    } else {
                        values.bg_removed = false;
                    }
                } else if (fileItem.type === "video") {
                    values.video_file = base64Data;
                    values.video_filename = fileName;
                }

                commands.push([0, 0, values]);
            }

            await this.props.record.update({
                [this.props.name]: commands
            });

            this.state.filesToUpload = [];
            
            this.notification.add(_t("Files uploaded successfully"), { type: "success" });
            this.closeUploadOptionsDialog();

        } catch (e) {
            this.notification.add(_t("Upload failed"), { type: "danger" });
        } finally {
            this.state.isUploadingFiles = false;
        }
    }

    async removeBackgroundFromFile(index) {
        const fileItem = this.state.filesToUpload[index];
        
        if (!fileItem || fileItem.type !== 'image') {
            this.notification.add(_t("Only images can have background removed"), { type: "warning" });
            return;
        }

        if (!fileItem.preview) {
            this.notification.add(_t("Please wait for preview to load"), { type: "warning" });
            return;
        }

        this.state.isRemovingBackground = true;

        try {
            let imageData = fileItem.preview;
            if (imageData.startsWith('data:')) {
                imageData = imageData.split(',')[1];
            }

            if (!fileItem.originalPreview) {
                fileItem.originalPreview = fileItem.preview;
            }

            const result = await this.orm.call(
                "product.image",
                "remove_background",
                [imageData]
            );

            if (result.success && result.data) {
                fileItem.preview = `data:image/png;base64,${result.data}`;
                fileItem.bgRemoved = true;
                fileItem.format = 'PNG';
                
                const blob = await fetch(fileItem.preview).then(r => r.blob());
                fileItem.file = new File([blob], fileItem.name.replace(/\.[^/.]+$/, ".png"), { type: 'image/png' });
                fileItem.size = (blob.size / (1024 * 1024)).toFixed(2);
                
                this.state.filesToUpload = [...this.state.filesToUpload];
                
                this.notification.add(_t("Background removed"), { type: "success" });
            } else {
                this.notification.add(_t("Failed: " + (result.error || "Unknown error")), { type: "danger" });
            }
        } catch (error) {
            this.notification.add(_t("Error: " + error.message), { type: "danger" });
        } finally {
            this.state.isRemovingBackground = false;
        }
    }

    async restoreBackgroundFromFile(index) {
        const fileItem = this.state.filesToUpload[index];
        
        if (!fileItem || !fileItem.originalPreview) {
            this.notification.add(_t("No original to restore"), { type: "warning" });
            return;
        }

        try {
            fileItem.preview = fileItem.originalPreview;
            fileItem.bgRemoved = false;
            
            const blob = await fetch(fileItem.preview).then(r => r.blob());
            const originalExt = fileItem.name.split('.').pop();
            fileItem.file = new File([blob], fileItem.name, { type: `image/${originalExt}` });
            fileItem.format = originalExt.toUpperCase();
            fileItem.size = (blob.size / (1024 * 1024)).toFixed(2);
            
            this.state.filesToUpload = [...this.state.filesToUpload];
            
            this.notification.add(_t("Original restored"), { type: "success" });
        } catch (error) {
            this.notification.add(_t("Error restoring"), { type: "danger" });
        }
    }

    openGalleryFromUpload(index) {
        this.state.currentIndex = index;
        this.state.selectedFileIndex = index;
        this.state.showDragZoneOnly = false;
        this.closeUploadOptionsDialog();
        this.openDialog();
    }

    // =================================================================
    // DRAG & DROP
    // =================================================================

    async onDrop(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.state.isDragging = false;

        const files = ev.dataTransfer.files;
        if (files.length === 0) return;

        const maxSize = 10 * 1024 * 1024;
        
        // Add files to preview array for review before saving
        for (const file of files) {
            if (file.size > maxSize) {
                this.notification.add(_t(`${file.name} exceeds 10MB limit`), { type: "warning" });
                continue;
            }

            const isImage = file.type.startsWith("image/");
            const isVideo = file.type.startsWith("video/");

            if (!isImage && !isVideo) {
                this.notification.add(_t(`${file.name} is not a valid image or video`), { type: "warning" });
                continue;
            }

            const fileObj = {
                file: file,
                name: file.name,
                size: (file.size / (1024 * 1024)).toFixed(2),
                type: isVideo ? 'video' : 'image',
                format: file.name.split('.').pop().toUpperCase(),
                preview: null,
                setPrimary: false,
                bgRemoved: false,
                originalPreview: null,
            };

            try {
                fileObj.preview = await getDataURLFromFile(file);
            } catch (error) {
                
            }

            this.state.filesToUpload.push(fileObj);
        }

        if (this.state.filesToUpload.length > 0) {
            this.state.currentIndex = 0;
            this.state.showDragZoneOnly = false;
            this.notification.add(_t(`${this.state.filesToUpload.length} file(s) ready.`), { type: "info" });
        }
    }

    onDragEnter(ev) { 
        ev.preventDefault(); 
        ev.stopPropagation(); 
        this.state.isDragging = true; 
    }

    onDragOver(ev) { 
        ev.preventDefault(); 
        ev.stopPropagation(); 
        this.state.isDragging = true; 
    }
    
    onDragLeave(ev) { 
        ev.preventDefault(); 
        ev.stopPropagation(); 
        if (!ev.currentTarget.contains(ev.relatedTarget)) {
            this.state.isDragging = false;
        }
    }

    onFileOpen() {
        if (this.fileInputGallery && this.fileInputGallery.el) {
            this.fileInputGallery.el.click();
        }
    }

    async onFileInputChange(ev) {
        const files = ev.target.files;
        if (files.length > 0) {
            await this.processFiles(files);
        }
        ev.target.value = "";
    }

    async processFiles(files) {
    
    if (this.state.isUploadingFiles) {
        this.notification.add(_t("Upload already in progress"), { type: "warning" });
        return;
    }

    this.state.isUploadingFiles = true;

    const commands = [];
    const maxSize = 10 * 1024 * 1024;
    const failedFiles = [];
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        if (file.size > maxSize) {
            failedFiles.push(`${file.name} (exceeds 10MB)`);
            continue;
        }

        const isImage = file.type.startsWith("image/");
        const isVideo = file.type.startsWith("video/");

        if (!isImage && !isVideo) {
            failedFiles.push(`${file.name} (invalid type)`);
            continue;
        }

        try {
            const matchingPreview = this.state.filesToUpload.find(f => 
                f.name === file.name || f.file === file
            );

            let base64Data;
            
            if (matchingPreview && matchingPreview.preview) {
                base64Data = matchingPreview.preview.split(',')[1];
            } else {
                const dataUrl = await getDataURLFromFile(file);
                base64Data = dataUrl.split(',')[1];
            }

            if (!base64Data) {
                failedFiles.push(`${file.name} (no data)`);
                continue;
            }

            const fileName = file.name || `media_${Date.now()}_${i}`;
            
            const vals = {
                name: fileName,
                upload_method: 'drag_drop',
                sequence: commands.length + 1,
                is_primary: matchingPreview?.setPrimary || false,
            };

            if (isImage) {
                vals.image_1920 = base64Data;
                
                if (matchingPreview && matchingPreview.bgRemoved && matchingPreview.originalPreview) {
                    vals.bg_removed = true;
                    vals.image_1920_original = matchingPreview.originalPreview.split(',')[1];
                } else {
                    vals.bg_removed = false;
                }
            } else if (isVideo) {
                vals.video_file = base64Data;
                vals.video_filename = fileName;
            }

            commands.push([0, 0, vals]);
            
        } catch (error) {
            failedFiles.push(`${file.name} (${error.message})`);
        }
    }

    if (failedFiles.length > 0) {
        this.notification.add(
            _t(`${failedFiles.length} file(s) could not be processed: ${failedFiles.join(', ')}`), 
            { type: "warning" }
        );
    }

    if (commands.length === 0) {
        this.notification.add(_t("No valid files to upload"), { type: "warning" });
        this.state.isUploadingFiles = false;
        return;
    }

    try {
        await this.props.record.update({
            [this.props.name]: commands
        });

        this.state.filesToUpload = [];

        const newIndex = this.mediaItems.length - commands.length;
        this.state.currentIndex = Math.max(0, newIndex);
        this.state.showDragZoneOnly = false;
        
        this.notification.add(
            _t(`${commands.length} file(s) added successfully`), 
            { type: "success" }
        );
        
    } catch (error) {
        const errorMsg = error.message || error.data?.message || "Unknown error";
        this.notification.add(
            _t(`Upload failed: ${errorMsg}`), 
            { type: "danger" }
        );
        console.error("Upload error details:", error);
    } finally {
        this.state.isUploadingFiles = false;
    }
}

    async savePreviewedFiles() {
    if (this.state.filesToUpload.length === 0) {
        this.notification.add(_t("No files to save"), { type: "warning" });
        return;
    }

    
    if (this.state.isUploadingFiles) {
        this.notification.add(_t("Upload already in progress"), { type: "warning" });
        return;
    }

    this.state.isUploadingFiles = true;

    const commands = [];
    const maxSize = 10 * 1024 * 1024;
    const failedFiles = [];
    
    for (let i = 0; i < this.state.filesToUpload.length; i++) {
        const fileItem = this.state.filesToUpload[i];
        
        // Validate file size
        if (fileItem.file && fileItem.file.size > maxSize) {
            failedFiles.push(`${fileItem.name} (exceeds 10MB)`);
            continue;
        }

        // Validate preview exists
        if (!fileItem.preview) {
            failedFiles.push(`${fileItem.name} (no preview data)`);
            continue;
        }

        try {
            const base64Data = fileItem.preview.split(',')[1];
            
            if (!base64Data) {
                failedFiles.push(`${fileItem.name} (invalid data)`);
                continue;
            }

            const fileName = fileItem.name || `media_${Date.now()}_${i}`;
            
            const vals = {
                name: fileName,
                upload_method: 'drag_drop',
                sequence: commands.length + 1,
                is_primary: fileItem.setPrimary || false,
            };

            if (fileItem.type === "image") {
                vals.image_1920 = base64Data;
                
                if (fileItem.bgRemoved && fileItem.originalPreview) {
                    vals.bg_removed = true;
                    vals.image_1920_original = fileItem.originalPreview.split(',')[1];
                } else {
                    vals.bg_removed = false;
                }
            } else if (fileItem.type === "video") {
                vals.video_file = base64Data;
                vals.video_filename = fileName;
            }

            commands.push([0, 0, vals]);
            
        } catch (error) {
            failedFiles.push(`${fileItem.name} (${error.message})`);
        }
    }

    
    if (failedFiles.length > 0) {
        this.notification.add(
            _t(`${failedFiles.length} file(s) could not be processed: ${failedFiles.join(', ')}`), 
            { type: "warning" }
        );
    }

    // If no valid commands, stop here
    if (commands.length === 0) {
        this.notification.add(_t("No valid files to save"), { type: "warning" });
        this.state.isUploadingFiles = false;
        return;
    }

    try {
       
        await this.props.record.update({
            [this.props.name]: commands
        });

        
        const savedCount = commands.length;
        this.state.filesToUpload = [];
        
       
        const newIndex = this.mediaItems.length - savedCount;
        this.state.currentIndex = Math.max(0, newIndex);
        this.state.showDragZoneOnly = false;
        
        
        this.notification.add(
            _t(`${savedCount} file(s) saved successfully`), 
            { type: "success" }
        );
        
        
        this.closeDialog();
        
    } catch (error) {
        // Show actual error message
        const errorMsg = error.message || error.data?.message || "Unknown error";
        this.notification.add(
            _t(`Save failed: ${errorMsg}`), 
            { type: "danger" }
        );
        
        
        
        
       
    } finally {
        this.state.isUploadingFiles = false;
    }
}

    // =================================================================
    // NAVIGATION
    // =================================================================

    nextMedia() {
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly) {
            if (this.state.currentIndex < this.state.filesToUpload.length - 1) {
                this.state.currentIndex++;
            } else {
                this.state.currentIndex = 0;
            }
            return;
        }

        if (this.state.currentIndex < this.mediaItems.length - 1) {
            this.state.currentIndex++;
        } else {
            this.state.currentIndex = 0;
        }
        this.state.isPlaying = false;
    }

    prevMedia() {
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly) {
            if (this.state.currentIndex > 0) {
                this.state.currentIndex--;
            } else {
                this.state.currentIndex = this.state.filesToUpload.length - 1;
            }
            return;
        }

        if (this.state.currentIndex > 0) {
            this.state.currentIndex--;
        } else {
            this.state.currentIndex = this.mediaItems.length - 1;
        }
        this.state.isPlaying = false;
    }

    selectThumbnail(index) {
        this.state.currentIndex = index;
    }

    onVideoTimeUpdate(ev) {
        const video = ev.target;
        if (video.duration > 0) {
            this.state.videoProgress = (video.currentTime / video.duration) * 100;
        }
    }

    onVideoEnded() {
        this.state.isPlaying = false;
        this.state.videoProgress = 0;
    }

    // =================================================================
    // MEDIA DELETION
    // =================================================================

    async removeCurrentMedia() {
        const record = this.currentItem;
        if (!record) return;

        try {
            const idToRemove = record.resId;
            
            if (!idToRemove || typeof idToRemove === 'string') {
                this.notification.add(_t("Cannot delete unsaved media. Save the record first."), { type: "warning" });
                return;
            }
            
            await this.props.record.update({
                [this.props.name]: [[2, idToRemove, 0]]
            });

            if (this.state.currentIndex >= this.mediaItems.length && this.mediaItems.length > 0) {
                this.state.currentIndex = this.mediaItems.length - 1;
            }

            this.notification.add(_t("Media removed"), { type: "info" });
        } catch (error) {
            this.notification.add(_t("Error removing media"), { type: "danger" });
        }
    }

    async deleteMediaItem(index) {
        const record = this.mediaItems[index];
        if (!record) return;

        try {
            const idToRemove = record.resId;
            
            if (!idToRemove || typeof idToRemove === 'string') {
                this.notification.add(_t("Cannot delete unsaved media. Save the record first."), { type: "warning" });
                return;
            }
            
            await this.props.record.update({
                [this.props.name]: [[2, idToRemove, 0]]
            });

            this.notification.add(_t("Media deleted successfully"), { type: "success" });
        } catch (error) {
            this.notification.add(_t("Error deleting media"), { type: "danger" });
        }
    }

    // =================================================================
    // BACKGROUND REMOVAL
    // =================================================================

    async removeBackground() {
        // Preview mode (files not yet saved)
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly && 
            this.state.currentIndex < this.state.filesToUpload.length) {
            
            const currentFile = this.state.filesToUpload[this.state.currentIndex];

            if (!currentFile || currentFile.type !== 'image') {
                this.notification.add(_t("Only images can have background removed"), { type: "warning" });
                return;
            }

            this.state.isRemovingBackground = true;

            try {
                let imageData = currentFile.preview;
                if (imageData.startsWith('data:')) {
                    imageData = imageData.split(',')[1];
                }

                if (!currentFile.originalPreview) {
                    currentFile.originalPreview = currentFile.preview;
                }

                const result = await this.orm.call(
                    "product.image",
                    "remove_background",
                    [imageData]
                );

                if (result.success && result.data) {
                    currentFile.preview = `data:image/png;base64,${result.data}`;
                    currentFile.bgRemoved = true;
                    
                    const blob = await fetch(currentFile.preview).then(r => r.blob());
                    currentFile.file = new File([blob], currentFile.name.replace(/\.[^/.]+$/, ".png"), { type: 'image/png' });
                    currentFile.format = 'PNG';
                    currentFile.size = (blob.size / (1024 * 1024)).toFixed(2);

                    this.state.filesToUpload = [...this.state.filesToUpload];

                    this.notification.add(_t("Background removed successfully"), { type: "success" });
                } else {
                    this.notification.add(_t("Failed to remove background: " + (result.error || "Unknown error")), { type: "danger" });
                }
            } catch (error) {
                this.notification.add(_t("Error removing background"), { type: "danger" });
            } finally {
                this.state.isRemovingBackground = false;
            }
            return;
        }
        
        // Saved record mode
        const currentRecord = this.currentItem;
        
        if (!currentRecord) {
            return;
        }
        
        const isSavedRecord = currentRecord.resId && typeof currentRecord.resId === 'number';
        
        if (this.isVideo()) {
            this.notification.add(_t("Only images can have background removed"), { type: "warning" });
            return;
        }

        if (!isSavedRecord) {
            this.notification.add(_t("Please save the form first before removing background"), { type: "warning" });
            return;
        }

        this.state.isRemovingBackground = true;

        try {
            const fetchResult = await this.orm.call(
                "product.image",
                "get_image_data",
                [currentRecord.resId]
            );
            
            if (!fetchResult.success || !fetchResult.data) {
                this.notification.add(_t("Failed to get image data"), { type: "danger" });
                this.state.isRemovingBackground = false;
                return;
            }
            
            const originalImageData = fetchResult.data;

            const bgRemoveResult = await this.orm.call(
                "product.image",
                "remove_background",
                [originalImageData]
            );

            if (bgRemoveResult.success && bgRemoveResult.data) {
                await this.orm.write(
                    "product.image",
                    [currentRecord.resId],
                    {
                        image_1920: bgRemoveResult.data,
                        image_1920_original: originalImageData,
                        bg_removed: true,
                    }
                );
                
                await this.props.record.update({
                    [this.props.name]: [[1, currentRecord.resId, {
                        bg_removed: true,
                    }]]
                });
                
                await this.props.record.load();
                
                this.state.updateTrigger++;
                
                this.notification.add(_t("Background removed successfully!"), { type: "success" });
            } else {
                this.notification.add(_t("Failed to remove background: " + (bgRemoveResult.error || "Unknown error")), { type: "danger" });
            }
        } catch (error) {
            this.notification.add(_t("Error removing background"), { type: "danger" });
        } finally {
            this.state.isRemovingBackground = false;
        }
    }

    async restoreBackground() {
        // Preview mode
        if (this.state.filesToUpload.length > 0 && !this.state.showDragZoneOnly) {
            const currentFile = this.state.filesToUpload[this.state.currentIndex];
            
            if (!currentFile || currentFile.type !== 'image') {
                this.notification.add(_t("Only images can be restored"), { type: "warning" });
                return;
            }

            if (!currentFile.originalPreview) {
                this.notification.add(_t("No original image to restore"), { type: "warning" });
                return;
            }

            try {
                currentFile.preview = currentFile.originalPreview;
                currentFile.bgRemoved = false;
                
                const blob = await fetch(currentFile.preview).then(r => r.blob());
                const originalExt = currentFile.name.split('.').pop();
                currentFile.file = new File([blob], currentFile.name, { type: `image/${originalExt}` });
                currentFile.format = originalExt.toUpperCase();
                currentFile.size = (blob.size / (1024 * 1024)).toFixed(2);
                
                this.state.filesToUpload = [...this.state.filesToUpload];
                
                this.notification.add(_t("Original image restored"), { type: "success" });
            } catch (error) {
                this.notification.add(_t("Error restoring image"), { type: "danger" });
            }
            return;
        }

        // Saved record mode
        const currentRecord = this.currentItem;
        
        if (!currentRecord) {
            return;
        }
        
        const isSavedRecord = currentRecord.resId && typeof currentRecord.resId === 'number';
        
        if (this.isVideo()) {
            this.notification.add(_t("Only images can be restored"), { type: "warning" });
            return;
        }

        if (!isSavedRecord) {
            this.notification.add(_t("Please save the form first before restoring background"), { type: "warning" });
            return;
        }

        this.state.isRestoringBackground = true;

        try {
            const fetchResult = await this.orm.call(
                "product.image",
                "get_original_image_data",
                [currentRecord.resId]
            );
            
            if (!fetchResult.success || !fetchResult.data) {
                this.notification.add(_t("No original image to restore"), { type: "warning" });
                this.state.isRestoringBackground = false;
                return;
            }
            
            const originalImageData = fetchResult.data;
            
            await this.orm.write(
                "product.image",
                [currentRecord.resId],
                {
                    image_1920: originalImageData,
                    bg_removed: false,
                }
            );
            
            await this.props.record.update({
                [this.props.name]: [[1, currentRecord.resId, {
                    bg_removed: false,
                }]]
            });
            
            await this.props.record.load();
            
            this.state.updateTrigger++;
            
            this.notification.add(_t("Original image restored successfully!"), { type: "success" });
            
        } catch (error) {
            this.notification.add(_t("Error restoring image"), { type: "danger" });
        } finally {
            this.state.isRestoringBackground = false;
        }
    }

    // =================================================================
    // UTILITIES
    // =================================================================

    isValidUrl(string) {
        if (string.startsWith('data:image/')) {
            return true;
        }
        
        try {
            const url = new URL(string);
            return url.protocol === "http:" || url.protocol === "https:";
        } catch (_) {
            return false;
        }
    }

    extractFilenameFromUrl(url) {
        try {
            const pathname = new URL(url).pathname;
            return pathname.split('/').pop() || 'media_file';
        } catch {
            return 'media_file';
        }
    }
}

registry.category("fields").add("enhanced_media_gallery_dialog", {
    component: EnhancedMediaGalleryDialog,
    displayName: _t("Enhanced Media Gallery (Dialog)"),
    supportedTypes: ["one2many"],
});
