# Q1000K PON setup (contribution candidate)

The open drivers need the Ethernet PON series and the three PON kmods. The
Q1000K profile installs `pon-mac-config`, which pulls those kmods in. Its
service starts disabled, with `gpon` selected. Loading the MAC does not start
activation. There is no OMCI daemon in this package.

GPON reached O5 and carried service on a Calix OLT in a downstream 6.18.55
kexec image. This does not validate the upstream UBI flash layout or a
sysupgrade. XGS-PON activation and service have model coverage only. The
2026-10-17 fixed hardware start reached O1 without a reset, on GPON fibre;
the earlier reset's exact cause remains under investigation. Do not infer
XGS-PON service support from that start.

## Firmware, supplied locally

No EN7572 firmware is included or downloaded by the build. On a build host,
install Python 3 and squashfs-tools 4.5 or newer (for `unsquashfs -cat`),
obtain the stock firmware yourself, and run from the OpenWrt checkout:

```sh
python3 scripts/en7572-firmware.py --url
python3 scripts/en7572-firmware.py QKX001-06.00.44.00.bin /tmp/pon-firmware
```

The tool verifies the stock image and both extracted files by SHA256. For
an already copied stock root filesystem, use `--dir <rootfs> <destination>`.
This reads firmware data; it does not execute stock programs. It needs no
access to the private development repository. `--url` only prints a location
and expected hash; it does not download anything.

For a local image build, copy the resulting `airoha/` directory into
`<openwrt>/files/lib/firmware/`. Keep that overlay and any image containing
it local: no redistribution licence has been established. Alternatively,
copy the two extracted files to the running unit:

```sh
ssh root@192.168.1.1 mkdir -p /lib/firmware/airoha
scp -O /tmp/pon-firmware/airoha/en7572-program.bin /tmp/pon-firmware/airoha/en7572-data.bin root@192.168.1.1:/lib/firmware/airoha/
```

These files persist only if stored in the unit's persistent filesystem;
an initramfs boot loses them. Missing firmware prevents a start. Firmware
can be installed before enabling the service without reloading the modules.

## Factory calibration and identity

Keep the original read-only `vendor` partition intact. The board DTS reads
the unit's 512-byte GPON and XGS-PON calibration cells at partition-relative
offsets `0x411000` and `0x412000`. The serial defaults script searches the
2 MiB factory store beginning at `0x400000` for its `fsan` record; it also
understands a separate `dsd` partition. It never writes MTD and preserves an
existing UCI serial. No serial, password, key or calibration bytes belong
in a contribution, shared image, bug report or branch.

UCI defaults also run on an initramfs boot. If the factory serial was not
populated, the read-only reader can be rerun manually:

```sh
sh /etc/uci-defaults/80-pon-identity
sh /etc/uci-defaults/81-pon-leds
```

Check the serial locally in `/etc/config/pon`; if the factory store is
missing or malformed, configure the unit's own identity manually. No
registration credentials are invented. A GPON password or XGS-PON
registration ID is operator-specific and must be supplied locally if needed.

## Explicit GPON activation

After supplying firmware, confirming the factory identity, and arranging
the OMCI agent and operator configuration:

```sh
uci set pon.mac.line_mode='gpon'
uci set pon.mac.enabled='1'
uci commit pon
/etc/init.d/pon enable
/etc/init.d/pon restart
```

The kernel exposes an `omci` transport netdev and the `airoha-pon-mac`
netlink family. An OMCI agent must provision GEM ports, T-CONTs and service
rules; activation alone provides no subscriber service. Agent packaging,
platform helpers and LuCI are separate contributions. This candidate does
not create a WAN bridge or change the LAN configuration.

To stop activation and retain that choice across boots:

```sh
uci set pon.mac.enabled='0'
uci commit pon
/etc/init.d/pon stop
```

`auto` probes both line modes and is deliberately not the initial setting
in this contribution. Select XGS-PON only as part of its separate hardware
validation. This package does not establish a supported flash installation
or recovery procedure.
