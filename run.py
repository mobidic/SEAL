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
