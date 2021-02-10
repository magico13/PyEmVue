class VueDevice(object):
    def __init__(self, gid=0, manId='', modelNum='', firmwareVersion=''):
        self.device_gid = gid
        self.manufacturer_id = manId
        self.model = modelNum
        self.firmware = firmwareVersion
        self.channels = []
        self.outlet = None

        #extra info
        self.device_name = ''
        self.zip_code = '00000'
        self.time_zone = ''
        self.usage_cent_per_kw_hour = 0.0
        self.peak_demand_dollar_per_kw = 0.0
        self.billing_cycle_start_day = 0
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
        if 'locationProperties' in js:
            self.populate_location_properties_from_json(js['locationProperties'])
        # 'devices' is empty in my system, will add support later if possible
        if 'channels' in js:
            # Channels are another subtype and the channelNum is used in other calls
            self.channels = []
            for chnl in js['channels']:
                self.channels.append(VueDeviceChannel().from_json_dictionary(chnl))
        # outlets are a special type
        if 'outlet' in js and js['outlet']:
            self.outlet = OutletDevice().from_json_dictionary(js['outlet'])
        return self
    
    def populate_location_properties_from_json(self, js):
        """Adds the values from the get_device_properties method."""
        if 'deviceName' in js: self.device_name = js['deviceName']
        if 'zipCode' in js: self.zip_code = js['zipCode']
        if 'timeZone' in js: self.time_zone = js['timeZone']
        if 'usageCentPerKwHour' in js: self.usage_cent_per_kw_hour = js['usageCentPerKwHour']
        if 'peakDemandDollarPerKw' in js: self.peak_demand_dollar_per_kw = js['peakDemandDollarPerKw']
        if 'billingCycleStartDay' in js: self.billing_cycle_start_day = js['billingCycleStartDay']
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

class VueDeviceChannelUsage(VueDeviceChannel):
    def __init__(self, gid=0, usage=0, channelNum='1,2,3'):
        self.device_gid = gid
        self.usage = usage
        self.channel_num = channelNum
        self.timestamp = None

    def from_json_dictionary(self, js):
        """Populate device channel usage data from a dictionary extracted from the response json."""
        if not js: return self
        if 'deviceGid' in js: self.device_gid = js['deviceGid']
        if 'channelNum' in js: self.channel_num = js['channelNum']
        if 'usage' in js:
            if 'value' in js['usage']:
                self.usage = js['usage']['value']
            if 'Timestamp' in js['usage'] and 'epochSecond' in js['usage']['Timestamp']:
                self.timestamp = js['usage']['Timestamp']['epochSecond']
        return self

class OutletDevice(object):
    def __init__(self, gid=0, on=False, parentGid=0, parentChannel=0):
        self.device_gid = gid
        self.outlet_on = on
        self.parent_device_gid = parentGid
        self.parent_channel_num = parentChannel
        self.schedules = []

    def from_json_dictionary(self, js):
        if 'deviceGid' in js: self.device_gid = js['deviceGid']
        if 'outletOn' in js: self.outlet_on = js['outletOn']
        if 'parentDeviceGid' in js: self.parent_device_gid = js['parentDeviceGid']
        if 'parentChannelNum' in js: self.parent_channel_num = js['parentChannelNum']
        # don't have support for schedules yet
        return self
    
    def as_dictionary(self):
        j = {}
        j['deviceGid'] = self.device_gid
        j['outletOn'] = self.outlet_on
        j['parentDeviceGid'] = self.parent_device_gid
        j['parentChannelNum'] = self.parent_channel_num
        return j
