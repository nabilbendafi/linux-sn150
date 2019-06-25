#!/usr/bin/env python3

import argparse
import logging
import sys
import textwrap
from pathlib import Path

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)

try:
    import serial
except ImportError as _:
    LOGGER.error('Failed to load module. Please install pyserial.')
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

    LOGGER.debug('Open %s file' % output)
    with open(output.as_posix(), 'w') as o:
        LOGGER.info('Open %s serial device' % device)
        try:
            with serial.Serial(device, baudrate=115200, timeout=1.0) as s:
                # Initialise SPI Flash read
                cmd = b'sf probe 1\n'
                LOGGER.debug('Send %s to %s' % (cmd, device))
                s.write(cmd)
                _ = s.readlines()

                start_address = '0x%08x' % 0x0  # 0x00000000
                for i in range(3):
                    cmd = b'sf read 0x08000000 %d 100\n' % (i*100)
                    LOGGER.debug('Send %s to %s' % (cmd, device))
                    s.write(cmd)
                    _ = s.readlines()

                    cmd = b'md 0x08000000\n'
                    LOGGER.debug('Send %s' % cmd)
                    s.write(cmd)
                    _ = s.readline()
                    lines = s.readlines()
                    for line in lines:
                        line = line.decode('utf-8')
                        if not line.startswith('SN150'):
                            LOGGER.debug('Send %s to %s' % (cmd, device))
                            o.write(line)
        except serial.serialutil.SerialException as se:
            LOGGER.error('Failed to open %s: %s' % (device, str(se)))


if __name__ == "__main__":
    # Rock'n'Roll
    main()
