{
  inputs,
  cell,
}:
inputs.nixpkgs.lib.evalModules
{
  modules = [
    cell.derivations.magneticsensortracking
  ];
  specialArgs = {
    inherit (inputs) dream2nix;
    packageSets = {
      inherit (inputs) nixpkgs;
      python = inputs.nixpkgs.python310;
    };
  };
}
#.config
#.groups
#.default
#.public
#.packages

