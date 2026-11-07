/* @odoo-module */

import { Component, useState, reactive, useRef,onWillStart, onWillUnmount, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

/*created global class for channelising (save and retrieve datas)*/
export const pimGlobalChannel = reactive({
    channel: {},
    record: false,
});

export class PimChannelisation extends Component {
    static template = "pim_channelization.PimChannelisation";
    static props = {
        root: { type: Object },
    };
    setup(){
        this.orm = useService('orm');
        this.action = useService('action');
        this.ChannelDrop = useRef("LanguagesDrop");
        this.input = useRef("search");
        /*-----------------------------------------------------*/
        this.state = useState({
            channels: [],
            filtered_channels: [],
            channel: false,
            show_drop: false,
        });
        onWillStart(async () => {
            var channels = await this.orm.call("platform.credentials", "get_all_active_channels", [])
            this.state.channels = channels;
            this.state.filtered_channels = channels;
            /*GET THE CHANNEL FROM CURRENT COMPANY*/
            var [_user] = await this.orm.searchRead("res.users",[['id','=', user.userId]],['m_channel_id'])
            this.state.channel = _user?.m_channel_id[0];
        });
        onMounted(async () => {
            this.handleClickOutside = this.handleClickOutsideChannel.bind(this);
        });
        onWillUnmount(() => {
            document.removeEventListener("click", this.handleClickOutsideChannel);
        });
    }
    ClickOpenChannels(){
        if(this.state.show_drop == true){
            this.state.show_drop = false;
            document.removeEventListener('click', this.handleClickOutside);
            return;
        }
        this.state.show_drop = true;
        setTimeout(() => {
            document.addEventListener('click', this.handleClickOutside);
        }, 0);
        return;
    }
    handleClickOutsideChannel(){
        const dropdown = this.ChannelDrop.el;
        if (dropdown && !dropdown.contains(ev.target)) {
            this.state.show_drop = false;
            document.removeEventListener('click', this.handleClickOutsideChannel);
        }
    }
    onSearchInput() {
        const query = this.input.el.value.toLowerCase();
        this.state.filtered_channels = this.state.channels.filter(channel =>
            channel.platform.toLowerCase().includes(query)
        );
    }
    async SelectChannel(channel){
        this.state.show_drop = false;
        this.state.channel = channel.id;
        await this.setChannel()
        const viewService = this.env.services.view;
        if (viewService?.clearCache) {
            viewService.clearCache();
        } else {
            this.env.bus.trigger("CLEAR-CACHES");
        }
        pimGlobalChannel.record = this.props.root.editedRecord;
        await this.action.doAction({
            type: 'ir.actions.client',
            tag: 'soft_reload',
        });
    }
    async setChannel(){
        /*UPDATE THE CHANNEL TO CURRENT COMPANY*/
        await this.orm.write("res.users", [user.userId], { m_channel_id: this.state.channel });
    }
    get currentChannel(){
        return this.state.channels.find(l => l.id == this.state.channel)
    }
}