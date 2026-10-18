# SPDX-License-Identifier: GPL-2.0-only

OTHER_MENU:=Other modules


define KernelPackage/pwm-airoha
  SUBMENU:=$(OTHER_MENU)
  TITLE:=Airoha AN7581 and AN7583 PWM
  DEPENDS:=@TARGET_airoha_an7581||TARGET_airoha_an7583
  KCONFIG:= \
        CONFIG_PWM=y \
        CONFIG_PWM_AIROHA=y \
        CONFIG_PWM_SYSFS=y
  FILES:= \
        $(LINUX_DIR)/drivers/pwm/pwm-airoha.ko
  AUTOLOAD:=$(call AutoProbe,pwm-airoha)
endef

define KernelPackage/pwm-airoha/description
 Kernel module to use the PWM channel on Airoha SoC
endef

$(eval $(call KernelPackage,pwm-airoha))

# The EN7581 PON kmods. The kernel side is the PON PHY driver
# and the EN7572 laser driver (drivers/phy/airoha/) and the PON MAC driver
# (drivers/net/ethernet/airoha/pon/), which needs the frame engine's PON mode (target patches 930-*).

define KernelPackage/phy-en7581-pon
  SUBMENU:=$(OTHER_MENU)
  TITLE:=Airoha EN7581 PON PHY
  DEPENDS:=@TARGET_airoha_an7581
  KCONFIG:=CONFIG_PHY_EN7581_PON
  FILES:=$(LINUX_DIR)/drivers/phy/airoha/phy-en7581-pon.ko
  AUTOLOAD:=$(call AutoProbe,phy-en7581-pon)
endef

define KernelPackage/phy-en7581-pon/description
 The PON PHY of the Airoha EN7581: the serdes facing the optical module and
 the line block behind it, for GPON and XGS-PON.
endef

$(eval $(call KernelPackage,phy-en7581-pon))

define KernelPackage/airoha-pon-mac
  SUBMENU:=$(NETWORK_DEVICES_MENU)
  TITLE:=Airoha EN7581 GPON and XGS-PON MAC
  DEPENDS:=@TARGET_airoha_an7581 +kmod-phy-en7581-pon +kmod-phy-en7572
  KCONFIG:=CONFIG_NET_AIROHA_PON_MAC
  FILES:=$(LINUX_DIR)/drivers/net/ethernet/airoha/pon/airoha-pon-mac.ko
  AUTOLOAD:=$(call AutoProbe,airoha-pon-mac)
endef

define KernelPackage/airoha-pon-mac/description
 The PON MACs of the Airoha EN7581, GPON (ITU-T G.984.3) and XGS-PON
 (ITU-T G.9807.1). The pon-mac-config package sets the ONU identity and
 starts it.
endef

$(eval $(call KernelPackage,airoha-pon-mac))

define KernelPackage/phy-en7572
  SUBMENU:=$(OTHER_MENU)
  TITLE:=Airoha EN7572 PON laser driver
  DEPENDS:=@TARGET_airoha_an7581
  KCONFIG:=CONFIG_PHY_EN7572
  FILES:=$(LINUX_DIR)/drivers/phy/airoha/phy-en7572.ko
  AUTOLOAD:=$(call AutoProbe,phy-en7572)
endef

define KernelPackage/phy-en7572/description
 The EN7572 laser driver of a PON optic, on I2C: loads the chip's firmware and
 the PON mode's calibration table, starts it, and limits the laser's drive
 when it runs hot. The firmware images are not part of this package.
endef

$(eval $(call KernelPackage,phy-en7572))
