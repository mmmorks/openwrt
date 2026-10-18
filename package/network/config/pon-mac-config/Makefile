#
# The ONU identity and line mode of an EN7581 PON MAC, kept in UCI.
#
# SPDX-License-Identifier: GPL-2.0-only

include $(TOPDIR)/rules.mk

PKG_NAME:=pon-mac-config
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0-only
PKG_MAINTAINER:=John Morkel <john@morkel.me>

include $(INCLUDE_DIR)/package.mk

define Package/pon-mac-config
  SECTION:=net
  CATEGORY:=Network
  TITLE:=EN7581 PON MAC configuration
  DEPENDS:=@TARGET_airoha_an7581 +kmod-airoha-pon-mac
  PKGARCH:=all
endef

define Package/pon-mac-config/description
 Sets the ONU serial number, password or registration ID, and line mode of
 the Airoha EN7581 PON MAC from /etc/config/pon, and starts it when enabled.
 On first boot it takes the serial number from the board's factory identity store
 when the board has one.
endef

define Package/pon-mac-config/conffiles
/etc/config/pon
endef

define Build/Compile
endef

define Package/pon-mac-config/install
	$(INSTALL_DIR) $(1)/etc/config $(1)/etc/init.d $(1)/etc/uci-defaults
	$(INSTALL_CONF) ./files/pon.config $(1)/etc/config/pon
	$(INSTALL_BIN) ./files/pon.init $(1)/etc/init.d/pon
	$(INSTALL_DATA) ./files/pon.defaults $(1)/etc/uci-defaults/80-pon-identity
endef

$(eval $(call BuildPackage,pon-mac-config))
