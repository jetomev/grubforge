#!/usr/bin/env bash
# Build grubForge's test VMs for other distributions (v2.0.0, #24).
#
# One VM per family, from the distribution's own cloud image, set up on first
# start by cloud-init: a test user, the qemu guest agent (so tests can run
# commands inside), and Python + Textual for grubForge. UEFI, like most real
# computers today. No sudo: images go into libvirt's "default" pool with
# `virsh vol-upload`. Each VM ends shut off with a snapshot "fresh".
#
#   scripts/make-test-vms.sh [debian ubuntu fedora opensuse]   (default: all four)
#
# Logs to logs/make-test-vms-<time>.log (+ -latest link); the last line says OK.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
log="logs/make-test-vms-$(date +%Y%m%d-%H%M%S).log"
ln -sfn "$(basename "$log")" logs/make-test-vms-latest.log
exec > >(tee "$log") 2>&1

V="virsh -c qemu:///system"
CACHE="$HOME/Downloads/grubforge-test-images"
mkdir -p "$CACHE"

declare -A URL OS PKGS
URL[debian]="https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2"
URL[ubuntu]="https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
URL[fedora]="https://dl.fedoraproject.org/pub/fedora/linux/releases/44/Cloud/x86_64/images/Fedora-Cloud-Base-Generic-44-1.7.x86_64.qcow2"
URL[opensuse]="https://download.opensuse.org/tumbleweed/appliances/openSUSE-Tumbleweed-Minimal-VM.x86_64-Cloud.qcow2"
OS[debian]="debian13"; OS[ubuntu]="ubuntu24.04"; OS[fedora]="fedora44"; OS[opensuse]="opensusetumbleweed"
PKGS[debian]="qemu-guest-agent python3-venv"
PKGS[ubuntu]="qemu-guest-agent python3-venv"
PKGS[fedora]="qemu-guest-agent python3"
PKGS[opensuse]="qemu-guest-agent python3"

want=("$@"); [ ${#want[@]} -eq 0 ] && want=(debian ubuntu fedora opensuse)

for d in "${want[@]}"; do
  name="gf-$d"
  echo "=== $name"
  if $V dominfo "$name" >/dev/null 2>&1; then
    echo "already exists — skipping (remove it first to rebuild)"
    continue
  fi
  img="$CACHE/$(basename "${URL[$d]}")"
  [ -s "$img" ] || curl -fL --retry 3 -o "$img" "${URL[$d]}"
  echo "image: $(du -h "$img" | cut -f1)"

  # cloud-init seed: who logs in, what to install, the agent switched on
  seed="$CACHE/$name-seed"; rm -rf "$seed"; mkdir -p "$seed"
  printf 'instance-id: %s\nlocal-hostname: %s\n' "$name" "$name" > "$seed/meta-data"
  {
    echo "#cloud-config"
    echo "users:"
    echo "  - name: gftest"
    echo "    plain_text_passwd: gftest"
    echo "    lock_passwd: false"
    echo "    sudo: ALL=(ALL) NOPASSWD:ALL"
    echo "    shell: /bin/bash"
    echo "package_update: true"
    echo "packages: [$(echo ${PKGS[$d]} | sed 's/ /, /g')]"
    echo "runcmd:"
    # Fedora: SELinux confines the guest agent, so test commands couldn't read
    # root's files. This throwaway test VM runs SELinux permissive (it still logs);
    # grubForge's helper runs unconfined under the targeted policy either way.
    echo "  - command -v setenforce >/dev/null && setenforce 0 || true"
    echo "  - test -f /etc/selinux/config && sed -i 's/^SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config || true"
    # openSUSE: the agent ships with guest-exec switched off; allow it in this test VM
    echo "  - test -f /usr/etc/sysconfig/qemu-ga && echo 'FILTER_RPC_ARGS=\"\"' > /etc/sysconfig/qemu-ga || true"
    echo "  - systemctl enable --now qemu-guest-agent || true"
    echo "  - systemctl restart qemu-guest-agent || true"
    echo "  - python3 -m venv /opt/gf && /opt/gf/bin/pip install -q textual rich"
    echo "  - touch /var/lib/gf-ready"
  } > "$seed/user-data"
  xorriso -as mkisofs -quiet -o "$CACHE/$name-seed.iso" -V cidata -J -r "$seed" 2>/dev/null

  # into libvirt's pool, no sudo
  size=$(stat -c %s "$img")
  $V vol-delete --pool default "$name.qcow2" >/dev/null 2>&1 || true
  $V vol-create-as default "$name.qcow2" "$size" --format qcow2 >/dev/null
  $V vol-upload --pool default "$name.qcow2" "$img"
  $V vol-resize --pool default "$name.qcow2" 12G >/dev/null
  iso_size=$(stat -c %s "$CACHE/$name-seed.iso")
  $V vol-delete --pool default "$name-seed.iso" >/dev/null 2>&1 || true
  $V vol-create-as default "$name-seed.iso" "$iso_size" --format raw >/dev/null
  $V vol-upload --pool default "$name-seed.iso" "$CACHE/$name-seed.iso"
  pool=$($V pool-dumpxml default | sed -n 's:.*<path>\(.*\)</path>.*:\1:p' | head -1)

  virt-install --connect qemu:///system --name "$name" --memory 2048 --vcpus 2 \
    --osinfo "${OS[$d]}" --import \
    --disk "path=$pool/$name.qcow2,bus=virtio" \
    --disk "path=$pool/$name-seed.iso,device=cdrom" \
    --network network=default --boot uefi \
    --channel unix,target.type=virtio,target.name=org.qemu.guest_agent.0 \
    --graphics none --noautoconsole

  echo "waiting for first-start setup (packages, Python, Textual)…"
  ok=""
  for i in $(seq 1 120); do
    if $V qemu-agent-command "$name" '{"execute":"guest-exec","arguments":{"path":"/usr/bin/test","arg":["-e","/var/lib/gf-ready"]}}' >/dev/null 2>&1; then
      sleep 5
      pid=$($V qemu-agent-command "$name" '{"execute":"guest-exec","arguments":{"path":"/usr/bin/test","arg":["-e","/var/lib/gf-ready"]}}' | sed 's/.*"pid":\([0-9]*\).*/\1/')
      sleep 2
      st=$($V qemu-agent-command "$name" "{\"execute\":\"guest-exec-status\",\"arguments\":{\"pid\":$pid}}")
      if echo "$st" | grep -q '"exitcode":0'; then ok=1; break; fi
    fi
    sleep 10
  done
  [ -n "$ok" ] || { echo "$name: setup did not finish in 20 minutes"; exit 1; }
  echo "$name: ready"
  $V shutdown "$name" >/dev/null
  for i in $(seq 1 30); do [ "$($V domstate "$name")" = "shut off" ] && break; sleep 3; done
  $V change-media "$name" sdb --eject --config >/dev/null 2>&1 || true
  $V snapshot-create-as "$name" fresh "first start done: gftest user, guest agent, /opt/gf venv with textual" >/dev/null \
    && echo "$name: snapshot 'fresh'" || echo "$name: snapshot not supported (UEFI nvram) — revert by re-running"
done
echo OK
