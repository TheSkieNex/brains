from utils.utils import ICON_URL

class Config:
    def __init__(self, dev: bool):
        self.dev = dev
        self.main_color = 0x9e22e3
        self.second_color = 0x3c2b40
        self.icon_url = ICON_URL

        self.ticket_channel_id = 1074718558552076469 if self.dev else 1233184738710388736
        self.ticket_category_id = 1232724511250583676 if self.dev else 1233428987057803395
        self.community_role_id = 1071117063411748935 if self.dev else 1125366325909409832
        self.welcome_channel_id = 1071115646257090580 if self.dev else 1125363834018873436
        self.modlog_channel_id = 1071115646257090580 if self.dev else 1233398121178857594
        self.guild_id = 1070804318485233766 if self.dev else 1125326451944738847

        self.owner_user_id = 530689295699148800
        self.organizer_role_id = 1070804523100143717 if self.dev else 1233168847968927744