class VueDevice(object):
    def __init__(self, gid=0, manId='', modelNum='', firmwareVersion=''):
        self.device_gid = gid
        self.manufacturer_id = manId
        self.model = modelNum
        self.firmware = firmwareVersion
        self.channels = []

    def from_json_dictionary(self, js):
        """Populate device data from a dictionary extracted from the response json."""
        if 'deviceGid' in js: self.device_gid = js['deviceGid']
        if 'manufacturerDeviceId' in js: self.manufacturer_id = js['manufacturerDeviceId']
        if 'model' in js: self.model = js['model']
        if 'firmware' in js: self.firmware = js['firmware']
        # 'devices' is empty in my system, will add support later if possible
        if 'channels' in js:
            # Channels are another subtype and the channelNum is used in other calls
            self.channels = []
            for chnl in js['channels']:
                self.channels.append(VueDeviceChannel().from_json_dictionary(chnl))
        return self

class VueDeviceChannel(object):
    def __init__(self, gid=0, name='', channelNum='1,2,3', channelMultiplier=1.0):
        self.device_gid = gid
        self.name = name
        self.channel_num = channelNum
        self.channel_multiplier = channelMultiplier

    def from_json_dictionary(self, js):
        """Populate device channel data from a dictionary extracted from the response json."""
        if 'deviceGid' in js: self.device_gid = js['deviceGid']
        if 'name' in js: self.name = js['name']
        if 'channelNum' in js: self.channel_num = js['channelNum']
        if 'channelMultiplier' in js: self.channel_multiplier = js['channelMultiplier']
        return self

class VuewDeviceChannelUsage(object):
    def __init__(self, gid=0, usage=0, channelNum='1,2,3'):
        self.device_gid = gid
        self.usage = usage
        self.channel_num = channelNum

    def from_json_dictionary(self, js):
        """Populate device channel usage data from a dictionary extracted from the response json."""
        if 'deviceGid' in js: self.device_gid = js['deviceGid']
        if 'usage' in js: self.usage = js['usage']
        if 'channelNum' in js: self.channel_num = js['channelNum']
        return self