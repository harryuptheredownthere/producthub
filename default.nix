{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    nodejs
    gcc
  ];

  shellHook = ''
    if [ ! -d "venv" ]; then
      python -m venv venv
    fi
    source venv/bin/activate
    pip install -r backend/requirements.txt
  '';
}