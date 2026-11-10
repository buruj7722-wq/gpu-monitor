"""Render a reviewable TLS proxy config; never install, reload or change a firewall."""

import argparse
import re
from pathlib import Path


def render(server_name: str, certificate: str, private_key: str, htpasswd: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?", server_name):
        raise ValueError("Use one explicit DNS hostname or IPv4 address")
    for path in [certificate, private_key, htpasswd]:
        if not re.fullmatch(r"/[A-Za-z0-9_./-]+", path) or ".." in Path(path).parts:
            raise ValueError(
                "Credential paths must be absolute and contain no config metacharacters"
            )
    result = (Path(__file__).resolve().parent.parent / "deploy/nginx.conf.template").read_text()
    for token, value in {
        "__SERVER_NAME__": server_name,
        "__CERTIFICATE__": certificate,
        "__PRIVATE_KEY__": private_key,
        "__HTPASSWD__": htpasswd,
    }.items():
        result = result.replace(token, value)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-name", required=True)
    parser.add_argument("--certificate", required=True)
    parser.add_argument("--private-key", required=True)
    parser.add_argument("--htpasswd", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = render(args.server_name, args.certificate, args.private_key, args.htpasswd)
    # Refuse accidental replacement of an existing local configuration.
    with args.output.open("x") as stream:
        stream.write(result)
    print(f"Prepared {args.output}; review and nginx -t before an approved installation")


if __name__ == "__main__":
    main()
