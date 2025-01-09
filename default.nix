{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    python311Packages.flask
    python311Packages.flask-cors
    python311Packages.requests
    python311Packages.urllib3
    python311Packages.charset-normalizer
    python311Packages.pandas
    python311Packages.openpyxl
    python311Packages.python-dotenv
    python311Packages.gunicorn
    python311Packages.pip
    python311Packages.setuptools
    python311Packages.wheel
    python311Packages.typing-extensions
    python311Packages.cryptography  # For secrets module
    python311Packages.python-dateutil  # For datetime handling
    python311Packages.six  # Common dependency
    python311Packages.certifi  # For requests
    python311Packages.idna  # For requests
    gcc
  ];

  shellHook = ''
    export PYTHONPATH=$PWD/.nix-profile/lib/python3.11/site-packages:$PYTHONPATH
    export PATH=$PWD/.nix-profile/bin:$PATH
  '';
}