import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { debounce } from "@web/core/utils/timing";
import { patch } from "@web/core/utils/patch";
import { VideoSelector } from '@html_editor/main/media/media_dialog/video_selector';

// Patch the VideoSelector component
patch(VideoSelector.prototype, {
    setup() {
        // Call the original setup method
        super.setup();

        // Add the 'uploaded' platform
        this.PLATFORMS.uploaded = "uploaded";

        // Extend OPTIONS to include 'uploaded' platform
        this.OPTIONS = {
            ...this.OPTIONS,
            autoplay: {
                ...this.OPTIONS.autoplay,
                platforms: [...this.OPTIONS.autoplay.platforms, "uploaded"],
            },
            loop: {
                ...this.OPTIONS.loop,
                platforms: [...this.OPTIONS.loop.platforms, "uploaded"],
            },
        };

        // Add uploadError to the state
        this.state.uploadError = "";

        // Bind the file upload handler
        this.onFileUploaded = this.onFileUploaded.bind(this);
    },
    async onFileUploaded(ev) {
        const file = ev.target.files[0];
        if (!file) return;

        this.state.uploadError = "";

        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("csrf_token", odoo.csrf_token || window.odoo.csrf_token); // Fallback if odoo.csrf_token isn’t set

            const response = await fetch("/web_editor/video_upload", {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest", // Add for Odoo CSRF
                },
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const responseData = await response.json();
            if (responseData.error) {
                this.state.uploadError = responseData.error;
                return;
            }

            this.state.urlInput = responseData.url;
            await this.updateVideo();
        } catch (error) {
            this.state.uploadError = _t("An error occurred while uploading the video: ") + error.message;
        }
    },
    async updateVideo() {
        if (!this.state.urlInput) {
            this.state.src = "";
            this.state.urlInput = "";
            this.state.options = [];
            this.state.platform = null;
            this.state.errorMessage = "";
            this.props.selectMedia({});
            return;
        }

        const embedMatch = this.state.urlInput.match(/(src|href)=["']?([^"']+)?/);
        const url = embedMatch ? embedMatch[2] : this.state.urlInput;

        const options = {};
        if (this.props.isForBgVideo) {
            Object.keys(this.OPTIONS).forEach((key) => {
                options[key] = true;
            });
        } else {
            for (const option of this.shownOptions) {
                options[option.id] = option.value;
            }
        }

        const {
            embed_url: src,
            video_id: videoId,
            params,
            platform,
        } = await this._getVideoURLData(url, options);

        if (platform === "uploaded") {
            this.state.src = url;
            this.state.platform = "uploaded";
        } else {
            this.state.src = src;
            this.state.platform = platform;
        }

        if (!src) {
            this.state.errorMessage = _t("The provided url is not valid");
        } else if (!platform) {
            this.state.errorMessage = _t("The provided url does not reference any supported video");
        } else {
            this.state.errorMessage = "";
        }
        this.props.errorMessages(this.state.errorMessage);

        const newOptions = [];
        if (platform && platform !== this.state.platform) {
            Object.keys(this.OPTIONS).forEach((key) => {
                if (this.OPTIONS[key].platforms.includes(platform)) {
                    const { label, description } = this.OPTIONS[key];
                    newOptions.push({ id: key, label, description });
                }
            });
        }

        this.state.src = src;
        this.state.options = newOptions;

        // Workaround: Map "uploaded" to a supported platform for selectMedia
        const mediaData = {
            id: src,
            src,
            platform: platform === "uploaded" ? "youtube" : platform, // Trick selectMedia
            videoId,
            params,
            originalPlatform: platform, // Preserve for rendering
        };

        try {
            this.props.selectMedia(mediaData);
        } catch (error) {
            if (error.message.includes("Unsupported platform")) {
                // Suppress the error and manually handle the uploaded video if needed
                this.state.errorMessage = "";
            } else {
                this.state.errorMessage = _t("Error processing video: ") + error.message;
            }
        }
    },


    async _getVideoURLData(url, options) {
    // Handle uploaded videos locally
        if (url.startsWith("/web/content/")) {
            return {
                embed_url: url,
                video_id: url.split("/").pop().split("?")[0],
                params: "",
                platform: "uploaded",
            };
        }
        // Fallback to RPC for external platforms
        return await rpc("/web_editor/video_url/data", {
            video_url: url,
            ...options,
        });
    },
});

// Add createElements as a static method
Object.assign(VideoSelector, {
    createElements(selectedMedia) {
        return selectedMedia.map((video) => {
            if (video.platform === "uploaded") {
                // Create a <video> element for uploaded videos
                const videoEl = document.createElement("video");
                videoEl.className = "o_video_dialog_iframe mw-100 mh-100 overflow-hidden shadow";
                videoEl.controls = true;
                videoEl.innerHTML = `
                    <source src="${video.src}" type="video/mp4">
                    ${_t("Your browser does not support the video tag.")}
                `;
                return videoEl;
            }
            // Fallback to original iframe implementation
            return this._super([video])[0];
        });
    },
});