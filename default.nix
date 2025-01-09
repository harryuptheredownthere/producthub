{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    python311Full
    python3Packages.flask
    python3Packages.requests
    # Add all your Python dependencies here
  ];
}