{
  description = "CONFIGURE-ME";
  inputs = {
    std = {
      url = "github:divnix/std";
      inputs.devshell.url = "github:numtide/devshell";
      inputs.nixago.url = "github:nix-community/nixago";
    };
    dream2nix.url = "github:purepani/dream2nix/pdm-make-lowercase-deps?dir=modules";
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };
  outputs = {std, ...} @ inputs:
    std.growOn {
      inherit inputs;
      cellsFrom = ./nix;
      cellBlocks = with std.blockTypes; [
        # Development Environments
        (nixago "configs")
        (devshells "shells")
        (functions "derivations")
        (installables "packages")
      ];
    }
    {
      packages = std.harvest inputs.self ["python" "packages" "config" "groups" "default" "public" "packages"];
      devShells = std.harvest inputs.self ["repo" "shells"];
    };
}
