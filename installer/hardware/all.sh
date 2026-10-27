run_logged "$ARCH_PATH/src/python/installer/hardware/package_gates.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/surface_firmware.py"
run_logged "$ARCH_INSTALL/hardware/gb10/sleep.sh"
run_logged "$ARCH_INSTALL/hardware/nvidia/dgx-spark-boot.sh"

run_logged "$ARCH_PATH/src/python/installer/hardware/network.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/wireless_regdom.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/apple_keyboard_fkeys.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/synaptic_touchpad.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/bluetooth.py"
run_logged "$ARCH_INSTALL/hardware/n1x.sh"
run_logged "$ARCH_PATH/src/python/installer/hardware/nvidia.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/nvidia_apps.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/vulkan.py"

run_logged "$ARCH_INSTALL/hardware/intel/video-acceleration.sh"
run_logged "$ARCH_PATH/src/python/installer/hardware/intel/lpmd.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/intel/thermald.py"
run_logged "$ARCH_INSTALL/hardware/intel/ipu7-camera.sh"
run_logged "$ARCH_INSTALL/hardware/intel/fred.sh"
run_logged "$ARCH_INSTALL/hardware/intel/fix-wifi7-eht.sh"
run_logged "$ARCH_PATH/src/python/installer/hardware/dell_xps13_ptl_speaker_firmware.py"

run_logged "$ARCH_INSTALL/hardware/fix-elgato-camlink-4k.sh"

# Rebuilds the boot image, so it follows camera module setup.
run_logged "$ARCH_INSTALL/hardware/dell-xps13-sidecar-amps.sh"

run_logged "$ARCH_INSTALL/hardware/asus/fix-asus-ptl-display-backlight.sh"
run_logged "$ARCH_INSTALL/hardware/asus/fix-asus-ptl-b9406-display.sh"
run_logged "$ARCH_INSTALL/hardware/asus/fix-asus-ptl-b9406-touchpad.sh"
run_logged "$ARCH_INSTALL/hardware/asus/fix-z13-touchpad.sh"
run_logged "$ARCH_INSTALL/hardware/asus/fix-asus-proart-p14-touchpad.sh"
run_logged "$ARCH_INSTALL/hardware/asus/fix-asus-proart-p14-speakers.sh"
run_logged "$ARCH_INSTALL/hardware/asus/fix-asus-proart-p14-fkeys.sh"
run_logged "$ARCH_INSTALL/hardware/fix-n1x-gpu-memory.sh"

run_logged "$ARCH_INSTALL/hardware/framework/qmk-hid.sh"

run_logged "$ARCH_INSTALL/hardware/apple/fix-spi-keyboard.sh"
run_logged "$ARCH_INSTALL/hardware/apple/fix-suspend-nvme.sh"
run_logged "$ARCH_INSTALL/hardware/apple/fix-t2.sh"
run_logged "$ARCH_INSTALL/hardware/apple/fix-brcmfmac-supplicant.sh"

# These write boot settings and build nothing, like n1x.sh: the installer's
# final limine-update builds the UKIs, and an image's first boot rebuilds once
# after its last step.
run_logged "$ARCH_INSTALL/hardware/qualcomm/dtb-uki.sh"
run_logged "$ARCH_PATH/src/python/installer/hardware/qualcomm/kernel_params.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/qualcomm/initramfs.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/qualcomm/firmware.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/qualcomm_camera.py"

run_logged "$ARCH_INSTALL/hardware/lenovo/fix-yoga-pro7-bass-speakers.sh"
run_logged "$ARCH_INSTALL/hardware/lenovo/yoga-slim7x.sh"
run_logged "$ARCH_INSTALL/hardware/lenovo/thinkpad-t14s-camera.sh"

run_logged "$ARCH_PATH/src/python/installer/hardware/broadcom_wifi.py"
run_logged "$ARCH_INSTALL/hardware/fix-surface-keyboard.sh"
run_logged "$ARCH_PATH/src/python/installer/hardware/tuxedo_backlight.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/speaker_tuning.py"
run_logged "$ARCH_INSTALL/hardware/pacman.sh"

run_logged "$ARCH_INSTALL/hardware/platform-setup.sh"
