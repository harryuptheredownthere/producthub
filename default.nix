{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    python311Full
    nodejs
    # Python packages
    python3Packages.flask
    python3Packages.flask-cors
    python3Packages.requests
    python3Packages.pandas
    python3Packages.openpyxl
    python3Packages.python-dotenv
    python3Packages.gunicorn
    # Development tools
    python3Packages.pip
    python3Packages.virtualenv
  ];
}