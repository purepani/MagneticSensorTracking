{
  description = "Moment Reconstruction of Image";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    devenv.url = "github:cachix/devenv";
  };
  outputs = {
    self,
    nixpkgs,
    flake-utils,
    devenv,
    ...
  } @ inputs:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {};

      packageName = "MagneticHeadTracking";
    in {
      devShell = devenv.lib.mkShell {
        inherit inputs pkgs;
        modules = [
          ({pkgs, ...}: {
            packages = [pkgs.zlib pkgs.python3 pkgs.nodejs pkgs.libgccjit pkgs.xorg.libX11 pkgs.libGLU pkgs.libGL pkgs.ffmpeg pkgs.xorg.libXrender pkgs.f2c];
            
            languages.python = {
              enable = true;
              venv.enable = true;
              poetry.enable = true;
            };
            languages.typescript = {
              enable = true;
            };
          })
        ];
      };
    });
}
