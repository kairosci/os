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

run_logged "$ARCH_PATH/src/python/installer/hardware/intel/video_acceleration.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/intel/lpmd.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/intel/thermald.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/intel/ipu7_camera.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/intel/fred.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/intel/wifi7_eht.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/dell_xps13_ptl_speaker_firmware.py"

run_logged "$ARCH_PATH/src/python/installer/hardware/elgato_camlink_4k.py"

# Rebuilds the boot image, so it follows camera module setup.
run_logged "$ARCH_INSTALL/hardware/dell-xps13-sidecar-amps.sh"

run_logged "$ARCH_PATH/src/python/installer/hardware/asus/panther_lake_display.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/asus/expertbook_b9406_touchpad.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/asus/rog_flow_z13_touchpad.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/asus/proart_p14_touchpad.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/asus/proart_p14_speakers.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/asus/proart_p14_fkeys.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/n1x_gpu_memory.py"

run_logged "$ARCH_PATH/src/python/installer/hardware/framework16_qmk_hid.py"

run_logged "$ARCH_PATH/src/python/installer/hardware/apple/macbook_spi_keyboard.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/apple/macbook_nvme_suspend.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/apple/t2.py"
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
run_logged "$ARCH_PATH/src/python/installer/hardware/lenovo/thinkpad_t14s_camera.py"

run_logged "$ARCH_PATH/src/python/installer/hardware/broadcom_wifi.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/surface_keyboard.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/tuxedo_backlight.py"
run_logged "$ARCH_PATH/src/python/installer/hardware/speaker_tuning.py"
run_logged "$ARCH_INSTALL/hardware/pacman.sh"

run_logged "$ARCH_INSTALL/hardware/platform-setup.sh"
