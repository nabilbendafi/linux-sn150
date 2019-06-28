#!/usr/bin/env python3

import argparse
import logging
import re
import sys
import textwrap
from pathlib import Path

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)

try:
    import hexdump
    import serial
except ImportError as _:
    LOGGER.error('Failed to load module. Please install hexdump and serialpyserial.')
    sys.exit(1)

parser = argparse.ArgumentParser(description='Dump SPI flash content',
                                 epilog='Report any issues to github.com/nabilbendafi',
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-d', '--device',
                    required=True,
                    help=textwrap.dedent('''\
        The device name of USB/Serial interface.
        ex: /dev/ttyUSB0'''))
parser.add_argument('-o', '--output',
                    dest='output',
                    default='dump_spi.kwb',
                    help='Output file')
parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='Increase output verbosity')

args = parser.parse_args()


def main():
    if args.verbose:
        LOGGER.setLevel(logging.DEBUG)

    cur_dir = Path.cwd()
    device = args.device
    output = Path(args.output)

    LOGGER.info('Open %s file' % output)
    with open(output.as_posix(), 'w') as o:
        LOGGER.info('Open %s serial device' % device)
        try:
            with serial.Serial(device, baudrate=115200, timeout=3.0) as s:
                # Send Ctrl-C for sanity
                cmd = b'\x03'
                LOGGER.debug('Send %s to %s' % (cmd, device))
                s.write(cmd)
                _ = s.readlines()  # Flush stdout content

                address_format = '%08x'  # 0x00000000
                offset = 0x0

                # Initialise SPI Flash read
                cmd = b'sf probe 1\n'
                LOGGER.debug('Send %s to %s' % (cmd, device))
                s.write(cmd)
                _ = s.readlines()  # Flush stdout content

                cmd = b'sf read 0x08000000 0 %x\n' % (512*1024)  # MX25L4005 with page size 64 KiB, total 512 KiB
                LOGGER.debug('Send %s to %s' % (cmd, device))
                s.write(cmd)
                _ = s.readlines()  # Flush stdout content

                cmd = b'md.b 0x08000000 %x\n' % (512*1024)  # MX25L4005 with page size 64 KiB, total 512 KiB
                LOGGER.debug('Send %s to %s' % (cmd, device))
                s.write(cmd)
                _ = s.readline()  # Flush stdout content

                while True:
                    line = s.readline()
                    line = line.decode('utf-8')
                    regex = '(?P<offset>[0-9a-fA-F]+): (?P<hex>([0-9a-fA-F]+ ){15}[0-9a-fA-F]+) *(?P<ascii>.*)'
                    regex = re.compile(regex)
                    m = regex.match(line)
                    if m:
                        line = m.groupdict()
                        hexa = ' '.join(re.findall('..',
                                                   line['hex'].replace(' ', '')))

                        line = "%s: %s  %s\n" % (address_format % (offset * 16),
                                                 hexa,
                                                 line['ascii'])
                        offset += 1
                        LOGGER.debug('Write %s to %s' % (line, output))
                        o.write(line)

                    # No more dump data
                    if not line:
                        break
        except serial.serialutil.SerialException as se:
            LOGGER.error('Failed to open %s: %s' % (device, str(se)))
            sys.exit(1)
    with open(output.as_posix(),'r') as txt:
        LOGGER.info('Convert dump to binrary')
        hex_dump = txt.read()
        with open(output.as_posix(),'bw') as binary:
            binary.write(hexdump.restore(hex_dump))


if __name__ == "__main__":
    # Rock'n'Roll
    main()
