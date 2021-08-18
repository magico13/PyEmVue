from pyemvue.pyemvue import PyEmVue

vue = PyEmVue()
vue.login(token_storage_file='keys.json')
print('Logged in. Authtoken follows:')
print(vue.cognito.id_token)
print()

devices = vue.get_devices()
outlets = vue.get_outlets()
for device in devices:
    print(device.device_gid, device.manufacturer_id, device.model, device.firmware)
    if device.outlet:
        print('Is an outlet! On? ', device.outlet.outlet_on)
    if device.ev_charger:
        print(f'Is an EV Charger! On? {device.ev_charger.charger_on} Charge rate: {device.ev_charger.charging_rate}A/{device.ev_charger.max_charging_rate}A')
    for chan in device.channels:
        print('\t', chan.device_gid, chan.name, chan.channel_num, chan.channel_multiplier)
    
if len(outlets) > 0:
    print("Discovered {} outlets. Press enter to turn them all off.".format(len(outlets)))
    input()
    for outlet in outlets:
        print("Turning off {}".format(outlet.device_gid))
        vue.update_outlet(outlet, False)
    print("Outlets turned off. Press enter to turn them on.")
    input()
    for outlet in outlets:
        print("Turning on {}".format(outlet.device_gid))
        vue.update_outlet(outlet, True)
else:
    print("No outlets discovered.")
