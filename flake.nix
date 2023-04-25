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
      pkgs = import nixpkgs {
        config.allowUnfree=true;
        imports = [
          ./cachix.nix
        ];
      };
      #pkgs_old = import nixpkgs_old {};
      jaxlib = pkgs.python3Packages.jaxlib.override {
            cudaSupport=true;
            };
      packageName = "MagneticHeadTracking";
    in {
      devShell = devenv.lib.mkShell {
        inherit inputs pkgs;
       
        modules = [
          ({pkgs, config, ...}: {
            packages = [pkgs.zlib pkgs.python3 pkgs.python3Packages.jax jaxlib pkgs.nodejs pkgs.libgccjit pkgs.xorg.libX11 pkgs.libGLU pkgs.libGL pkgs.ffmpeg pkgs.xorg.libXrender pkgs.f2c pkgs.cudatoolkit];
            env.JUPYTER_PATH = "${config.env.DEVENV_STATE}/venv/share/jupyter";
            env.JUPYTER_CONFIG_DIR = "${config.env.DEVENV_STATE}/venv/etc/jupyter";
            languages.python = {
              enable = true;
              venv.enable = true;
              poetry.enable = true;
            };
            languages.typescript = {
              enable = true;
            };
            enterShell = ''
              export LD_LIBRARY_PATH=/usr/lib/wsl/lib:$LD_LIBRARY_PATH
              export CUDA_PATH=${pkgs.cudatoolkit}
              export CUBLAS_LIB=$CUDA_PATH/lib64/libcublas.so
            '';

          })
        ];
      };
    });
}
