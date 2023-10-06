{
  inputs,
  cell,
}:
(inputs.nixpkgs.lib.evalModules
  {
    modules = [
      cell.derivations.magneticsensortracking
    ];
    specialArgs = {
      inherit (inputs) dream2nix;
      packageSets.nixpkgs = inputs.nixpkgs;
    };
  })
#.config
#.groups
#.default
#.public
#.packages
