class VueDevice(object):
    def __init__(self, gid=0, manId='', modelNum='', firmwareVersion=''):
        self.device_gid = gid
        self.manufacturer_id = manId
        self.model = modelNum
        self.firmware = firmwareVersion
        self.channels = []

        #extra info
        self.device_name = ''
        self.zip_code = '00000'
        self.time_zone = ''
        self.usage_cent_per_kw_hour = 0.0
        self.peak_demand_dollar_per_kw = 0.0
        self.solar = False
        self.air_conditioning = 'false'
        self.heat_source = ''
        self.location_sqft = '0'
        self.num_electric_cars = '0'
        self.location_type = ''
        self.num_people = ''
        self.swimming_pool = 'false'
        self.hot_tub = 'false'


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
    
    def populate_location_properties_from_json(self, js):
        """Adds the values from the get_device_properties method."""
        if 'deviceName' in js: self.device_name = js['deviceName']
        if 'zipCode' in js: self.zip_code = js['zipCode']
        if 'timeZone' in js: self.time_zone = js['timeZone']
        if 'usageCentPerKwHour' in js: self.usage_cent_per_kw_hour = js['usageCentPerKwHour']
        if 'peakDemandDollarPerKw' in js: self.peak_demand_dollar_per_kw = js['peakDemandDollarPerKw']
        if 'solar' in js: self.solar = js['solar']
        if 'locationInformation' in js and js['locationInformation']:
            li = js['locationInformation']
            if 'airConditioning' in li: self.air_conditioning = li['airConditioning']
            if 'heatSource' in li: self.heat_source = li['heatSource']
            if 'locationSqFt' in li: self.location_sqft = li['locationSqFt']
            if 'numElectricCars' in li: self.num_electric_cars = li['numElectricCars']
            if 'locationType' in li: self.location_type = li['locationType']
            if 'numPeople' in li: self.num_people = li['numPeople']
            if 'swimmingPool' in li: self.swimming_pool = li['swimmingPool']
            if 'hotTub' in li: self.hot_tub = li['hotTub']

class VueDeviceChannel(object):
    def __init__(self, gid=0, name='', channelNum='1,2,3', channelMultiplier=1.0, channelTypeGid=0):
        self.device_gid = gid
        self.name = name
        self.channel_num = channelNum
        self.channel_multiplier = channelMultiplier
        self.channel_type_gid = channelTypeGid

    def from_json_dictionary(self, js):
        """Populate device channel data from a dictionary extracted from the response json."""
        if 'deviceGid' in js: self.device_gid = js['deviceGid']
        if 'name' in js: self.name = js['name']
        if 'channelNum' in js: self.channel_num = js['channelNum']
        if 'channelMultiplier' in js: self.channel_multiplier = js['channelMultiplier']
        if 'channelTypeGid' in js: self.channel_type_gid = js['channelTypeGid']
        return self

class VuewDeviceChannelUsage(object):
    def __init__(self, gid=0, usage=0, channelNum='1,2,3'):
        self.device_gid = gid
        self.usage = usage
        self.channel_num = channelNum

    def from_json_dictionary(self, js):
        """Populate device channel usage data from a dictionary extracted from the response json."""
        if 'deviceGid' in js: self.device_gid = js['deviceGid']
        if 'usage' in js: self.usage = js['usage'] or 0
        if 'channelNum' in js: self.channel_num = js['channelNum']
        return self