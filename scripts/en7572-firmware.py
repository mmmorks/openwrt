#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""en7572-firmware.py - install the EN7572 laser driver's two firmware images from the
Q1000K's own stock firmware, so nobody has to redistribute them.

The phy-en7572 driver requests airoha/en7572-program.bin and airoha/en7572-data.bin. Neither
image is in linux-firmware and neither may be shipped by us. Both sit, byte for byte, in the
operator's public stock firmware file for the Q1000K and in the root filesystem of every unit
running it. This tool takes either one, finds the two images by size and sha256 (it does not
rely on where the stock filesystem keeps them), and writes them under the names the driver
requests.

Usage:
  en7572-firmware.py <stock firmware .bin> <dest>
      check the .bin's sha256, cut its squashfs out, find both images in it, and write
      <dest>/airoha/en7572-program.bin and <dest>/airoha/en7572-data.bin.
  en7572-firmware.py --dir <stock root filesystem> <dest>
      the same, from a directory: a stock root filesystem copied off a unit, or unpacked.
  en7572-firmware.py --url
      print where the stock firmware file can be downloaded, and its sha256.

<dest> is the directory that holds airoha/, e.g. an OpenWrt build's files/lib/firmware or
/lib/firmware on the unit. Exit status: 0 written, 2 refused (wrong input, an image not found
or found twice, a missing tool); nothing is written unless both images were found.

--manifest <file> replaces the built-in expectations (lines `image <sha256>`,
`program <size> <sha256>`, `data <size> <sha256>`), for the self-test and for a later
firmware release.
"""
import argparse
import hashlib
import os
import struct
import subprocess
import sys
import tempfile

URL = ('https://internethelp.centurylink.com/internethelp/modems/Q1000K/firmware/'
       'QKX001-06.00.44.00.bin')

# What the stock firmware file and the two images hash to (QKX001-06.00.44.00; QKX002-06.01.25.00
# carries the same two images).
EXPECT = {
    'image': 'dfdd23ffa8cbab9f3338835083d5a27c2ef0e27130d47b5d4a283d69df038972',
    'program': (15232, '5a8a4bbae5f70c1e615ba0aa1c2a1dce654611d3205d2fa983bf41e6cdadb4a1'),
    'data': (56, '21618dc3694a1e6f6b28c7da7141964dea1d6e57f2d2956bbe72a780ca6166a4'),
}

OUT_NAMES = {'program': 'en7572-program.bin', 'data': 'en7572-data.bin'}
UNSQUASHFS = os.environ.get('UNSQUASHFS', 'unsquashfs')
SQ_PREFIX = 'squashfs-root/'


class Refused(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_manifest(path):
    exp = {}
    with open(path) as f:
        for line in f:
            w = line.split()
            if not w or w[0].startswith('#'):
                continue
            if w[0] == 'image' and len(w) == 2:
                exp['image'] = w[1].lower()
            elif w[0] in OUT_NAMES and len(w) == 3:
                exp[w[0]] = (int(w[1]), w[2].lower())
            else:
                raise Refused('%s: cannot read line: %s' % (path, line.rstrip()))
    for k in ('image', 'program', 'data'):
        if k not in exp:
            raise Refused('%s: no %s line' % (path, k))
    return exp


def cut_squashfs(blob):
    """The stock file holds one squashfs; its superblock gives its length (u64 LE at +40)."""
    off = blob.find(b'hsqs')
    if off < 0:
        raise Refused('no squashfs in the firmware file')
    if blob.find(b'hsqs', off + 1) >= 0:
        raise Refused('more than one squashfs magic in the firmware file')
    if off + 48 > len(blob):
        raise Refused('the squashfs superblock is cut short')
    used = struct.unpack_from('<Q', blob, off + 40)[0]
    if used <= 0 or off + used > len(blob):
        raise Refused('the squashfs claims %d bytes at %d, past the end of the file' % (used, off))
    return blob[off:off + used]


def run_unsquashfs(args):
    try:
        p = subprocess.run([UNSQUASHFS] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise Refused('%s not found (squashfs-tools)' % UNSQUASHFS)
    if p.returncode != 0:
        raise Refused('%s %s failed: %s' % (UNSQUASHFS, args[0], p.stderr.decode(errors='replace').strip()))
    return p.stdout


def candidates_squashfs(sqfs, sizes):
    """Yield the bytes of every regular file whose size is one we look for."""
    listing = run_unsquashfs(['-lls', sqfs]).decode(errors='replace')
    for line in listing.splitlines():
        w = line.split(None, 5)
        if len(w) < 6 or not w[0].startswith('-') or not w[2].isdigit():
            continue
        if int(w[2]) not in sizes or not w[5].startswith(SQ_PREFIX):
            continue
        yield run_unsquashfs(['-no-wildcards', '-cat', sqfs, w[5][len(SQ_PREFIX):]])


def candidates_dir(root, sizes):
    for d, _ds, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            if os.path.getsize(p) in sizes:
                with open(p, 'rb') as fh:
                    yield fh.read()


def find_images(blobs, exp):
    found = {}
    for data in blobs:
        h = sha256(data)
        for k in OUT_NAMES:
            if (len(data), h) == exp[k]:
                if k in found:
                    continue  # the same bytes twice is the same image
                found[k] = data
    missing = [k for k in OUT_NAMES if k not in found]
    if missing:
        raise Refused('not found: the %s image (size %s, sha256 %s)' % (
            ' and the '.join(missing), ', '.join(str(exp[k][0]) for k in missing),
            ', '.join(exp[k][1] for k in missing)))
    return found


def write_images(found, dest):
    outdir = os.path.join(dest, 'airoha')
    os.makedirs(outdir, exist_ok=True)
    for k, name in OUT_NAMES.items():
        path = os.path.join(outdir, name)
        tmp = path + '.tmp'
        with open(tmp, 'wb') as f:
            f.write(found[k])
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
        print('%s  %s' % (sha256(found[k]), path))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--url', action='store_true', help='print the download location and stop')
    ap.add_argument('--dir', help='take the images from this stock root filesystem directory')
    ap.add_argument('--manifest', help='expected sha256 and sizes (see the module text)')
    ap.add_argument('inputs', nargs='*', help='<stock firmware .bin> <dest>, or <dest> with --dir')
    a = ap.parse_args(argv)
    try:
        exp = read_manifest(a.manifest) if a.manifest else EXPECT
        if a.url:
            print('%s\nsha256 %s' % (URL, exp['image']))
            return 0
        want = 1 if a.dir else 2
        if len(a.inputs) != want:
            ap.error('want %s' % ('<dest>' if a.dir else '<stock firmware .bin> <dest>'))
        sizes = {exp[k][0] for k in OUT_NAMES}
        if a.dir:
            if not os.path.isdir(a.dir):
                raise Refused('%s is not a directory' % a.dir)
            found = find_images(candidates_dir(a.dir, sizes), exp)
        else:
            with open(a.inputs[0], 'rb') as f:
                blob = f.read()
            if sha256(blob) != exp['image']:
                raise Refused('%s is not the expected stock firmware (sha256 %s, want %s; '
                              'download: %s)' % (a.inputs[0], sha256(blob), exp['image'], URL))
            with tempfile.TemporaryDirectory() as t:
                sqfs = os.path.join(t, 'root.sqfs')
                with open(sqfs, 'wb') as f:
                    f.write(cut_squashfs(blob))
                found = find_images(candidates_squashfs(sqfs, sizes), exp)
        write_images(found, a.inputs[-1])
    except (Refused, OSError) as e:
        print('en7572-firmware: refused: %s' % e, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
