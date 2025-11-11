import sounddevice as sd


def list_audio_devices():
    print("Available audio devices:")
    devices = sd.query_devices()
    print(devices)
    return devices


def verify_device(device_id):
    try:
        device_info = sd.query_devices(device_id)
        print(f"\nUsing device {device_id}: {device_info['name']}")
        return True
    except Exception as e:
        print(f"Error: Device {device_id} not found - {e}")
        return False
