# Raspberry Pi IP Camera Setup with MediaMTX and Auto IR-Cut

This guide describes the process of setting up a Raspberry Pi-based IP camera using:

- Camera module (e.g., OV5647)
- MediaMTX (formerly rtsp-simple-server)
- Auto IR-Cut control
- Optional watchdog and scheduled reboot

---

## 🔧 Initial Setup

```bash
sudo raspi-config
```

Enable the camera and I2C interface.

---

## 🎥 Check Camera Availability

### List cameras

```bash
rpicam-vid --list-cameras
```
or
```bash
libcamera-vid --list-cameras
```

Output:
```text
Available cameras
-----------------
0 : ov5647 [2592x1944 10-bit GBRG] (/base/soc/i2c0mux/i2c@1/ov5647@36)
    Modes: 'SGBRG10_CSI2P' : 640x480 [58.92 fps - (16, 0)/2560x1920 crop]
                             1296x972 [46.34 fps - (0, 0)/2592x1944 crop]
                             1920x1080 [32.81 fps - (348, 434)/1928x1080 crop]
                             2592x1944 [15.63 fps - (0, 0)/2592x1944 crop]

```

### Check video devices

```bash
v4l2-ctl --list-devices
```

Output:
```text
unicam (platform:20801000.csi):
	/dev/video0
	/dev/media0
```

### Check driver info

```bash
v4l2-ctl --all
```

Output:
```text
Driver Info:
	Driver name      : unicam
	Card type        : unicam
	Bus info         : platform:20801000.csi
	Driver version   : 6.12.20
	Capabilities     : 0xa5a00001
		Video Capture
		Metadata Capture
		Read/Write
		Streaming
		Extended Pix Format
		Device Capabilities
	Device Caps      : 0x25200001
		Video Capture
		Read/Write
		Streaming
		Extended Pix Format
Media Driver Info:
	Driver name      : unicam
	Model            : unicam
	Serial           : 
	Bus info         : platform:20801000.csi
	Media version    : 6.12.20
	Hardware revision: 0x00000000 (0)
	Driver version   : 6.12.20
Interface Info:
	ID               : 0x03000005
	Type             : V4L Video
Entity Info:
	ID               : 0x00000003 (3)
	Name             : unicam-image
	Function         : V4L2 I/O
	Flags            : default
	Pad 0x01000004   : 0: Sink
	  Link 0x02000007: from remote pad 0x1000002 of entity 'ov5647 10-0036' (Camera Sensor): Data, Enabled, Immutable
Priority: 2
Video input : 0 (unicam-image: ok)
Format Video Capture:
	Width/Height      : 2592/1944
	Pixel Format      : 'pGAA' (10-bit Bayer GBGB/RGRG Packed)
	Field             : None
	Bytes per Line    : 3264
	Size Image        : 6345216
	Colorspace        : Raw
	Transfer Function : Default (maps to None)
	YCbCr/HSV Encoding: Default (maps to ITU-R 601)
	Quantization      : Default (maps to Full Range)
	Flags             : 
```

### Check I2C info

```bash
sudo apt update
sudo apt install i2c-tools
i2cdetect -y 1
```

Output:
```text
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- 23 -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --    
```

---

## 📸 Test Camera Streaming with VLC (OPTIONAL)

```bash
sudo apt install vlc
```

### rpicam

```bash
rpicam-vid -o - -t 0 | cvlc -vvv stream:///dev/stdin --sout '#standard{access=http,mux=ts,dst=:8160}' :demux=h264
```

### libcamera

```bash
libcamera-vid --framerate 15 --width 1296 --height 972 -o - -t 0 | cvlc -vvv stream:///dev/stdin --sout '#standard{access=http,mux=ts,dst=:8160}' :demux=h264 --h264-fps=15
```

Access test stream at: `http://<pi-cam-ip>:8160`

---

## 💡 Disable Camera LED

Edit:

```bash
sudo nano /boot/firmware/config.txt
```

Add:

```text
disable_camera_led=1
```

---

## 📦 Required Packages

```bash
sudo apt upgrade
sudo apt install git python3-psutil python3-smbus libfreetype6
```

---

## 🚀 MediaMTX Installation

```bash
wget https://github.com/bluenviron/mediamtx/releases/download/v1.12.0/mediamtx_v1.12.0_linux_armv6.tar.gz
tar -xzf mediamtx_v1.12.0_linux_armv6.tar.gz
sudo mv mediamtx /usr/local/bin/
```

### Create Configuration File

```yaml
# mediamtx.yml
authInternalUsers:
  - user: test
    pass: test

paths:
  cam:
    source: rpiCamera
    rpiCameraWidth: 1920
    rpiCameraHeight: 1080
```

Save as:

```bash
sudo mv mediamtx.yml /usr/local/etc/
```

Test
```bash
mediamtx /usr/local/etc/mediamtx.yml
```

Access test stream at: `http://<pi-cam-ip>:8888/cam/`

---

## 🌗 Auto IR-Cut Filter Control

### Test GPIO

```bash
cat /sys/kernel/debug/gpio
```

output
``` text
 gpio-542 (NC                  )
 gpio-543 (NC                  )
 gpio-544 (CAM_GPIO1           )
 gpio-545 (NC                  )
 gpio-546 (NC                  )
```

```bash
echo 544 > /sys/class/gpio/export
echo 0 > /sys/class/gpio/gpio544/value 
echo 1 > /sys/class/gpio/gpio544/value
```

### Install Auto IR-Cut script

```bash
git clone https://github.com/uncle-yura/pi-ip-cam.git
python pi-ip-cam/auto-ir-cut/auto-ir-cut.py
sudo mv pi-ip-cam/auto-ir-cut/ /opt/
```

---

## 🛠 Add Auto-Run to MediaMTX

Edit:

```bash
sudo nano /usr/local/etc/mediamtx.yml
```

Add:

```yaml
runOnInit: python /opt/auto-ir-cut/auto-ir-cut.py 5 verbose
runOnInitRestart: yes
```

Test:
```bash
mediamtx /usr/local/etc/mediamtx.yml
```

Output:
```text
2025/04/22 12:23:31 INF MediaMTX v1.12.0
2025/04/22 12:23:31 INF configuration loaded from /usr/local/etc/mediamtx.yml
2025/04/22 12:23:31 INF [RTSP] listener opened on :8554 (TCP), :8000 (UDP/RTP), :8001 (UDP/RTCP)
2025/04/22 12:23:32 INF [path cam] [RPI Camera source] started
2025/04/22 12:23:32 INF [path cam] runOnInit command started
[0:35:02.941736006] [1057]  INFO Camera camera_manager.cpp:327 libcamera v0.4.0+53-29156679-dirty (2025-04-14T07:14:37UTC)
[0:35:03.137972706] [1059]  WARN RPiSdn sdn.cpp:40 Using legacy SDN tuning - please consider moving SDN inside rpi.denoise
[0:35:03.180907203] [1059]  INFO RPI vc4.cpp:447 Registered camera /base/soc/i2c0mux/i2c@1/ov5647@36 to Unicam device /dev/media0 and ISP device /dev/media1
[0:35:03.194868039] [1057]  INFO Camera camera.cpp:1202 configuring streams: (0) 1296x972-YUV420
[0:35:03.197565008] [1059]  INFO RPI vc4.cpp:622 Sensor: /base/soc/i2c0mux/i2c@1/ov5647@36 - Selected sensor format: 1296x972-SGRBG10_1X10 - Selected unicam format: 1296x972-pgAA
using hardware H264 encoder
2025/04/22 12:23:33 INF [path cam] [RPI Camera source] ready: 1 track (H264)
Light level: 0.00 lx, threshold: 5
Light level: 0.00 lx, threshold: 5
Light level: 0.00 lx, threshold: 5
Light level: 0.00 lx, threshold: 5
Light level: 0.00 lx, threshold: 5
Light level: 0.00 lx, threshold: 5
```

Edit:

```bash
sudo nano /usr/local/etc/mediamtx.yml
```

Remove `verbose` and adjust `threshold`:

```yaml
runOnInit: python /opt/auto-ir-cut/auto-ir-cut.py 5
runOnInitRestart: yes
```

---

## 🧩 Systemd Service for MediaMTX

Create service file:

```bash
sudo tee /etc/systemd/system/mediamtx.service >/dev/null << EOF
[Unit]
Wants=network.target
[Service]
ExecStart=/usr/local/bin/mediamtx /usr/local/etc/mediamtx.yml
[Install]
WantedBy=multi-user.target
EOF
```

Enable service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mediamtx
sudo systemctl start mediamtx
```

---

## 🛡️ Enable Watchdog

Edit:

```bash
sudo nano /boot/firmware/config.txt
```

Add:

```text
dtparam=watchdog=on
```

Edit:

```bash
sudo nano /etc/systemd/system.conf
```

Set:

```text
RuntimeWatchdogSec=10
RebootWatchdogSec=2min
```

Install and configure:

```bash
sudo apt install watchdog
sudo nano /etc/watchdog.conf
```

Set:

```text
watchdog-device = /dev/watchdog
watchdog-timeout = 10
interface = eth0
min-memory = 30000
allocatable-memory = 6000
```

Enable:

```bash
sudo systemctl enable watchdog
sudo systemctl start watchdog
```

---

## 🔁 Daily Reboot (Optional)

```bash
sudo crontab -e
```

Add:

```text
30 0 * * * /sbin/shutdown -r now
```

---

## Links:

https://www.raspberrypi.com/products/raspberry-pi-zero-w/

https://www.waveshare.com/wiki/RPi_IR-CUT_Camera

https://github.com/bluenviron/mediamtx

--- 

## ✅ Done!

--- 
