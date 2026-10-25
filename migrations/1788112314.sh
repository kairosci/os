echo "Point rc-channel installs at the rc package repository"

# pacman-rc.conf shipped with [arch] pointing at the edge repository, a
# leftover from when release candidates published there. Candidates now publish
# to the dedicated rc channel, so a machine on the rc mirror was taking its
# arch packages from edge. Repoint only a conf that still carries the
# shipped pairing: an administrator who chose another combination keeps it.
if grep -q "https://rc-mirror.github.com/kairosci/os/" /etc/pacman.d/mirrorlist &&
  grep -q "^Server = https://pkgs.github.com/kairosci/os/edge/" /etc/pacman.conf; then
  sudo sed -i "s|^Server = https://pkgs.github.com/kairosci/os/edge/|Server = https://pkgs.github.com/kairosci/os/rc/|" /etc/pacman.conf
  echo "Switched the [arch] repository to the rc channel to match this machine's rc mirror."
fi
