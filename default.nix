{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    python311Packages.flask
    python311Packages.flask-cors
    python311Packages.requests
    python311Packages.pandas
    python311Packages.openpyxl
    python311Packages.python-dotenv
    python311Packages.gunicorn
    python311Packages.pip
    gcc
  ];

  shellHook = ''
    export PYTHONPATH=$PWD/.nix-profile/lib/python3.11/site-packages:$PYTHONPATH
  '';
}
