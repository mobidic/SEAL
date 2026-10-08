# (c) 2025, Charles VAN GOETHEM <c-vangoethem (at) chu-montpellier (dot) fr>
#
# This file is part of SEAL
# 
# SEAL db - Simple, Efficient And Lite database for NGS
# Copyright (C) 2025  Charles VAN GOETHEM - MoBiDiC - CHU Montpellier
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
from seal import app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SEAL: Simple, Efficient And Lite database for NGS")
    group_input = parser.add_argument_group('Options')
    group_input.add_argument(
        '-d',
        '--debug',
        default=False,
        action='store_true',
        help="Active debug mode"
    )
    group_input.add_argument(
        '-p',
        '--port',
        default=5000,
        help="Choose port for SEAL"
    )
    args = parser.parse_args()
    app.run(debug=args.debug, port=args.port)
