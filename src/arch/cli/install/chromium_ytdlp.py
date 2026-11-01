from arch.cli.install.native_messaging import install_native_messaging_host


def install_chromium_ytdlp_main() -> int:
  return install_native_messaging_host(__name__.rsplit(".", maxsplit=1)[-1])
