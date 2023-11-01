/*
This file holds reproducible shells with commands in them.

They conveniently also generate config files in their startup hook.
*/
{
  inputs,
  cell,
}: let
  #inherit (inputs.std) lib;
  lib = inputs.nixpkgs.lib // inputs.std.lib // builtins;
  #package-set = ps: with ps; (lib.attrsets.attrValues inputs.cells.python.packages.config.groups.default.public.packages);
  #  package-set = ps: [inputs.cells.python.packages.config.groups.default...public];
  #  python = inputs.cells.python.packages.config.deps.python3.withPackages package-set;
in {
  # Tool Homepage: https://numtide.github.io/devshell/
  default = lib.dev.mkShell {
    name = "Magnetic Sensor Dev Shell";
    #imports = [
    #  inputs.std.std.devshellProfiles.default
    #];

    # Tool Homepage: https://nix-community.github.io/nixago/
    # This is Standard's devshell integration.
    # It runs the startup hook when entering the shell.
    #nixago =
    #lib.lists.zipListsWith (f: a: f a)
    #(map lib.dev.mkNixago (with lib.cfg; [
    #conform
    #treefmt
    #editorconfig
    #githubsettings
    #lefthook
    #mdbook
    #]))
    #[
    #{data = {inherit (inputs) cells;};}
    #cell.configs.treefmt
    #cell.configs.editorconfig
    #cell.configs.githubsettings
    #cell.configs.lefthook
    #cell.configs.mdbook
    #(lib.cfg.treefmt cell.configs.treefmt)
    #(lib.cfg.editorconfig cell.configs.editorconfig)
    #(lib.cfg.githubsettings cell.configs.githubsettings)
    #(lib.cfg.lefthook cell.configs.lefthook)
    #(lib.cfg.mdbook cell.configs.mdbook)
    #];
    packages = [
      inputs.nixpkgs.pdm
      inputs.nixpkgs.stdenv.cc.cc.lib
      inputs.nixpkgs.zlib
      #inputs.nixpkgs.python39
      #inputs.nixpkgs.python310Packages.virtualenv
      #python
    ];
    #++ (lib.attrsets.attrValues inputs.cells.python.packages.config.groups.default.public.packages);
    env = [
      {
        name = "LD_LIBRARY_PATH";
        prefix = "${inputs.nixpkgs.zlib}/lib:${inputs.nixpkgs.lib.makeLibraryPath [inputs.nixpkgs.stdenv.cc.cc.lib]}";
      }
    ];

    imports = [inputs.std.std.devshellProfiles.default];
    commands = [
      #{
      #category = "rendering";
      #package = inputs.nixpkgs.mdbook;
      #}
    ];
  };
}
